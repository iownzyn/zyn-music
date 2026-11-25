# Saya Music
import asyncio
import contextlib
import glob
import os
import re
from typing import Dict, Optional

import aiofiles
import aiohttp
from aiohttp import TCPConnector
from yt_dlp import YoutubeDL

from SayaMusic.core.dir import CACHE_DIR, DOWNLOAD_DIR
from SayaMusic.utils.cookie_handler import COOKIE_PATH as _COOKIES_FILE
from SayaMusic.utils.tuning import CHUNK_SIZE, SEM
from config import API_KEY, API_URL, VIDEO_API_URL
from SayaMusic.logging import LOGGER

LOGGER = LOGGER(__name__)

USE_AUDIO_API = bool(API_URL and API_KEY)
USE_VIDEO_API = bool(VIDEO_API_URL and API_KEY)
_inflight: Dict[str, asyncio.Future] = {}
_inflight_lock = asyncio.Lock()
_session: Optional[aiohttp.ClientSession] = None
_session_lock = asyncio.Lock()
YOUTUBE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def log_download_source(title: str, source: str) -> None:
    LOGGER.info(f"Track '{title}' - Downloaded by {source}")


def extract_video_id(link: str) -> str:
    if not link:
        return ""
    s = link.strip()
    if YOUTUBE_ID_RE.match(s):
        return s
    if "v=" in s:
        return s.split("v=")[-1].split("&")[0]
    last = s.split("/")[-1].split("?")[0]
    if YOUTUBE_ID_RE.match(last):
        return last
    return ""


def get_cookie_file() -> Optional[str]:
    try:
        if _COOKIES_FILE and os.path.exists(_COOKIES_FILE) and os.path.getsize(_COOKIES_FILE) > 0:
            return _COOKIES_FILE
    except Exception:
        pass
    return None


def media_download_dir(media_type: str) -> str:
    """Base cache for a media type; audio and video never share cache entries."""
    folder = "video" if media_type == "video" else "audio"
    path = os.path.join(DOWNLOAD_DIR, folder)
    os.makedirs(path, exist_ok=True)
    return path


def provider_download_dir(media_type: str, provider: str) -> str:
    """Isolate API and yt-dlp output so racing providers cannot overwrite each other."""
    path = os.path.join(media_download_dir(media_type), provider)
    os.makedirs(path, exist_ok=True)
    return path


def find_cached_file(video_id: str, media_type: str) -> Optional[str]:
    if not video_id:
        return None
    extensions = (
        ("mp4", "mkv", "webm") if media_type == "video"
        else ("mp3", "m4a", "webm", "opus")
    )
    # Prefer provider-isolated caches, then the previous media-specific layout,
    # and finally safe legacy files in the original downloads directory.
    directories = (
        provider_download_dir(media_type, "ytdlp"),
        provider_download_dir(media_type, "api"),
        media_download_dir(media_type),
        DOWNLOAD_DIR,
    )
    for directory in directories:
        for ext in extensions:
            path = os.path.join(directory, f"{video_id}.{ext}")
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                return path
    return None


def get_ytdlp_base_opts(output_dir: str = DOWNLOAD_DIR) -> Dict[str, object]:
    os.makedirs(output_dir, exist_ok=True)
    opts = {
        "outtmpl": f"{output_dir}/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "overwrites": False,
        "continuedl": True,
        "noprogress": True,
        "concurrent_fragment_downloads": 16,
        "http_chunk_size": 1 << 20,
        "socket_timeout": 15,
        "retries": 1,
        "fragment_retries": 1,
        "cachedir": str(CACHE_DIR),
        "ignoreerrors": True,
        "merge_output_format": "mp4"
    }
    if cookiefile := get_cookie_file():
        opts["cookiefile"] = cookiefile
    return opts


async def get_http_session() -> aiohttp.ClientSession:
    global _session
    if _session and not _session.closed:
        return _session
    async with _session_lock:
        if _session and not _session.closed:
            return _session
        timeout = aiohttp.ClientTimeout(total=600, sock_connect=20, sock_read=60)
        connector = TCPConnector(limit=0, ttl_dns_cache=300, enable_cleanup_closed=True)
        _session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return _session


async def close_http_session() -> None:
    global _session
    async with _session_lock:
        if _session and not _session.closed:
            await _session.close()
        _session = None


async def download_file(url: str, out_path: str) -> Optional[str]:
    if not url:
        return None

    # Write to a temporary file and atomically publish only complete downloads.
    # This prevents a failed API transfer from becoming a poisoned cache hit.
    temp_path = f"{out_path}.part"
    try:
        os.makedirs(os.path.dirname(out_path) or DOWNLOAD_DIR, exist_ok=True)
        session = await get_http_session()
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            async with aiofiles.open(temp_path, "wb") as file:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    if chunk:
                        await file.write(chunk)

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) <= 0:
            return None
        os.replace(temp_path, out_path)
        return out_path
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        LOGGER.warning("API media download failed: %s", type(exc).__name__)
        return None
    finally:
        with contextlib.suppress(OSError):
            if os.path.exists(temp_path):
                os.remove(temp_path)


async def api_download_audio(link: str) -> Optional[str]:
    if not USE_AUDIO_API:
        return None
    vid = extract_video_id(link)
    if not vid:
        return None
    poll_url = f"{API_URL}/song/{vid}?api={API_KEY}"
    try:
        session = await get_http_session()
        while True:
            async with session.get(poll_url) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                status = str(data.get("status", "")).lower()
                if status == "downloading":
                    await asyncio.sleep(1.0)
                    continue
                if status != "done":
                    return None
                dl_url = data.get("link")
                fmt = data.get("format", "webm")
                safe_fmt = re.sub(r"[^a-zA-Z0-9]", "", str(fmt)) or "webm"
                out_path = os.path.join(provider_download_dir("audio", "api"), f"{vid}.{safe_fmt}")
                return await download_file(dl_url, out_path)
    except Exception:
        return None


async def api_download_video(link: str) -> Optional[str]:
    if not USE_VIDEO_API:
        return None
    vid = extract_video_id(link)
    if not vid:
        return None
    poll_url = f"{VIDEO_API_URL}/video/{vid}?api={API_KEY}"
    try:
        session = await get_http_session()
        while True:
            async with session.get(poll_url) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                status = str(data.get("status", "")).lower()
                if status == "downloading":
                    await asyncio.sleep(1.0)
                    continue
                if status != "done":
                    return None
                dl_url = data.get("link")
                fmt = data.get("format", "mp4")
                safe_fmt = re.sub(r"[^a-zA-Z0-9]", "", str(fmt)) or "mp4"
                out_path = os.path.join(provider_download_dir("video", "api"), f"{vid}.{safe_fmt}")
                return await download_file(dl_url, out_path)
    except Exception:
        return None


def get_final_path_from_info(info: Dict, output_dir: str = DOWNLOAD_DIR) -> Optional[str]:
    vid = info.get("id")
    if not vid:
        return None
    ext = info.get("ext")
    if ext:
        p = os.path.join(output_dir, f"{vid}.{ext}")
        if os.path.exists(p):
            return p
    matches = [
        path
        for path in glob.glob(os.path.join(output_dir, f"{vid}.*"))
        if os.path.isfile(path)
        and not path.endswith((".part", ".ytdl", ".temp"))
        and os.path.getsize(path) > 0
    ]
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0] if matches else None


def download_with_ytdlp_sync(link: str, fmt: str, media_type: str) -> Optional[str]:
    """Download with a preferred format, then retry using a compatible fallback."""
    formats = [fmt]
    if fmt.startswith("bestaudio"):
        formats.append("bestaudio/best")
    elif "bestvideo" in fmt:
        formats.append("best[height<=?720][width<=?1280]/best")

    last_error = None
    for selected_format in dict.fromkeys(formats):
        try:
            output_dir = provider_download_dir(media_type, "ytdlp")
            opts = get_ytdlp_base_opts(output_dir)
            opts["format"] = selected_format
            # Let yt-dlp raise extraction/download errors so provider fallback can run.
            opts["ignoreerrors"] = False
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                if info:
                    if path := get_final_path_from_info(info, output_dir):
                        return path
        except Exception as exc:
            last_error = exc
            LOGGER.warning(
                "yt-dlp attempt failed (format=%s): %s",
                selected_format,
                type(exc).__name__,
            )

    if last_error:
        LOGGER.error("All yt-dlp format attempts failed: %s", type(last_error).__name__)
    return None


async def run_with_semaphore(coro):
    async with SEM:
        return await coro


async def deduplicate_download(key: str, runner):
    # Do not hold the lock while waiting for another task's download.
    async with _inflight_lock:
        fut = _inflight.get(key)
        owner = fut is None
        if owner:
            fut = asyncio.get_running_loop().create_future()
            _inflight[key] = fut

    if not owner:
        return await asyncio.shield(fut)

    try:
        result = await runner()
        if not fut.done():
            fut.set_result(result)
        return result
    except asyncio.CancelledError:
        if not fut.done():
            fut.set_result(None)
        raise
    except Exception as exc:
        LOGGER.warning("Download failed for %s: %s", key, type(exc).__name__)
        if not fut.done():
            fut.set_result(None)
        return None
    finally:
        async with _inflight_lock:
            if _inflight.get(key) is fut:
                _inflight.pop(key, None)


async def race_ytdlp_and_api(yt_task, api_task, title: str):
    pending = {yt_task, api_task}
    while pending:
        done, pending = await asyncio.wait(
            pending, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            try:
                result = task.result()
            except asyncio.CancelledError:
                continue
            except Exception as exc:
                LOGGER.warning(
                    "Download provider failed for '%s': %s",
                    title,
                    type(exc).__name__,
                )
                continue

            if result and os.path.exists(result):
                source = "yt-dlp" if task is yt_task else "API"
                log_download_source(title, source)
                for other in pending:
                    other.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
                return result
    return None


async def yt_dlp_download(link: str, type: str, title: str = "") -> Optional[str]:
    loop = asyncio.get_running_loop()
    vid = extract_video_id(link)
    if cached := find_cached_file(vid, type):
        if title:
            LOGGER.info(f"Track '{title}' - Served from cache")
        return cached

    if type == "audio":
        key = f"audio:{link}"

        async def run():
            ytdlp_task = asyncio.create_task(
                run_with_semaphore(
                    loop.run_in_executor(None, download_with_ytdlp_sync, link, "bestaudio[ext=webm][acodec=opus]", "audio")
                )
            )
            api_task = asyncio.create_task(api_download_audio(link)) if USE_AUDIO_API else None
            if api_task:
                return await race_ytdlp_and_api(ytdlp_task, api_task, title or "Unknown")
            result = await ytdlp_task
            if result and title:
                log_download_source(title, "yt-dlp")
            return result

        return await deduplicate_download(key, run)

    elif type == "video":
        key = f"video:{link}"

        async def run():
            ytdlp_task = asyncio.create_task(
                run_with_semaphore(
                    loop.run_in_executor(None, download_with_ytdlp_sync, link, "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio)", "video")
                )
            )
            api_task = asyncio.create_task(api_download_video(link)) if USE_VIDEO_API else None
            if api_task:
                return await race_ytdlp_and_api(ytdlp_task, api_task, title or "Unknown")
            result = await ytdlp_task
            if result and title:
                log_download_source(title, "yt-dlp")
            return result

        return await deduplicate_download(key, run)

    return None

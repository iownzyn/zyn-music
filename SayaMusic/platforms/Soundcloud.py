# Saya Music
import asyncio
import re
from typing import Any, Dict, Optional, Tuple, Union

from yt_dlp import YoutubeDL

from SayaMusic.utils.downloader import yt_dlp_download
from SayaMusic.utils.formatters import seconds_to_min


_SC_RE = re.compile(r"^https?://(soundcloud\.com|on\.soundcloud\.com)/.+", re.I)


class SoundAPI:
    def __init__(self):
        # Cache resolved SoundCloud matches to avoid repeating provider searches.
        self._search_cache = {}
        self._search_cache_ttl = 600

    async def valid(self, link: str) -> bool:
        return bool(link and _SC_RE.match(link))

    async def _extract_info(self, url: str) -> Dict[str, Any]:
        def _run(u: str):
            opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": True,
            }
            with YoutubeDL(opts) as ydl:
                return ydl.extract_info(u, download=False)

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, _run, url)

        _type = str(info.get("_type", ""))
        if _type in ("url", "url_transparent") and info.get("url"):
            info = await loop.run_in_executor(None, _run, info["url"])

        return info

    async def search_and_download(self, query: str) -> Union[Tuple[Dict[str, Any], str], bool]:
        """Resolve a close SoundCloud catalogue match and download its playable audio."""
        import difflib
        import os
        import re

        query = " ".join((query or "").split()).strip()
        if not query:
            return False

        cache_key = query.casefold()
        cached = self._search_cache.get(cache_key)
        if cached:
            cached_at, cached_details, cached_path = cached
            if (
                asyncio.get_running_loop().time() - cached_at < self._search_cache_ttl
                and os.path.isfile(cached_path)
                and os.path.getsize(cached_path) > 0
            ):
                return dict(cached_details), cached_path
            self._search_cache.pop(cache_key, None)

        def _search(q: str):
            opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": True,
                "extract_flat": "in_playlist",
            }
            with YoutubeDL(opts) as ydl:
                data = ydl.extract_info(f"scsearch10:{q}", download=False)
            return (data or {}).get("entries") or []

        try:
            loop = asyncio.get_running_loop()
            entries = await asyncio.wait_for(
                loop.run_in_executor(None, _search, query), timeout=18
            )
        except Exception:
            return False

        # Rank results instead of blindly downloading the first SoundCloud hit.
        def score(entry):
            title = str(entry.get("title") or "").casefold()
            uploader = str(entry.get("uploader") or entry.get("artist") or "").casefold()
            candidate = f"{title} {uploader}".strip()
            q = query.casefold()
            ratio = difflib.SequenceMatcher(None, q, candidate).ratio()
            q_tokens = set(re.findall(r"[a-z0-9]+", q))
            c_tokens = set(re.findall(r"[a-z0-9]+", candidate))
            overlap = len(q_tokens & c_tokens) / max(len(q_tokens), 1)
            return (overlap * 0.7) + (ratio * 0.3)

        entries = sorted(entries, key=score, reverse=True)
        seen = set()
        for entry in entries[:5]:
            url = entry.get("webpage_url") or entry.get("url")
            if not url:
                continue
            if not str(url).startswith("http"):
                url = f"https://soundcloud.com/{str(url).lstrip('/')}"
            if url in seen:
                continue
            seen.add(url)
            try:
                result = await asyncio.wait_for(self.download(url), timeout=28)
            except Exception:
                result = False
            if result:
                details, file_path = result
                if not file_path or not os.path.isfile(file_path):
                    continue
                self._search_cache[cache_key] = (
                    asyncio.get_running_loop().time(), dict(details), file_path
                )
                if len(self._search_cache) > 256:
                    oldest = min(
                        self._search_cache,
                        key=lambda key: self._search_cache[key][0],
                    )
                    self._search_cache.pop(oldest, None)
                return details, file_path
        return False

    async def download(self, url: str) -> Union[Tuple[Dict[str, Any], str], bool]:
        try:
            info = await self._extract_info(url)
        except Exception:
            return False

        if not info or info.get("_type") == "playlist":
            return False

        title = (info.get("title") or "SoundCloud").strip()
        try:
            duration_sec = int(info.get("duration") or 0)
        except Exception:
            duration_sec = 0

        uploader = info.get("uploader") or ""
        thumb = (
            info.get("thumbnail")
            or (info.get("thumbnails") or [{}])[0].get("url")
            or ""
        )

        out_path: Optional[str] = await yt_dlp_download(url, type="audio", title=title)
        if not out_path:
            return False

        details = {
            "title": title,
            "duration_sec": duration_sec,
            "duration_min": seconds_to_min(max(duration_sec, 0)),
            "uploader": uploader,
            "thumb": thumb,
            "filepath": out_path,
        }
        return details, out_path

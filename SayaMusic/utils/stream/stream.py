# Saya Music
import os
import re
from difflib import SequenceMatcher
from random import randint

import aiohttp
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from SayaMusic import Carbon, SoundCloud, YouTube, app
from SayaMusic.core.call import StreamController
from SayaMusic.misc import db
from SayaMusic.utils.database import add_active_video_chat, is_active_chat
from SayaMusic.utils.exceptions import AssistantErr
from SayaMusic.utils.inline import aq_markup, close_markup, stream_markup
from SayaMusic.utils.pastebin import SAYABIN
from SayaMusic.utils.stream.queue import put_queue, put_queue_index
from SayaMusic.utils.thumbnails import get_thumb
from SayaMusic.utils.errors import capture_internal_err


def _normalize_track_name(value: str) -> str:
    value = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", (value or "").lower())
    value = re.sub(r"\b(official|video|audio|lyrics?|visualizer|4k|hd|full song)\b", " ", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


async def _jamendo_search_track(query: str):
    """Find a close Jamendo catalogue match and return its licensed stream URL."""
    client_id = getattr(config, "JAMENDO_CLIENT_ID", "")
    if not client_id or not query:
        return None

    params = {
        "client_id": client_id,
        "format": "json",
        "limit": 10,
        "namesearch": query,
        "audioformat": "mp32",
        "include": "licenses",
    }
    timeout = aiohttp.ClientTimeout(total=12)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.jamendo.com/v3.0/tracks/", params=params
            ) as response:
                if response.status != 200:
                    print(f"Jamendo search failed: HTTP {response.status}")
                    return None
                payload = await response.json(content_type=None)
    except Exception as exc:
        print(f"Jamendo search error: {type(exc).__name__}")
        return None

    if (payload.get("headers") or {}).get("status") != "success":
        return None

    wanted = _normalize_track_name(query)
    best, best_score = None, 0.0
    for track in payload.get("results", []):
        audio_url = track.get("audio")
        track_name = track.get("name") or ""
        if not audio_url or not audio_url.startswith("https://") or not track_name:
            continue
        candidate = _normalize_track_name(track_name)
        score = SequenceMatcher(None, wanted, candidate).ratio()
        wanted_words, candidate_words = set(wanted.split()), set(candidate.split())
        if wanted_words:
            score = max(score, len(wanted_words & candidate_words) / len(wanted_words))
        if score > best_score:
            best, best_score = track, score

    # Avoid playing an unrelated catalogue result for a popular YouTube query.
    return best if best and best_score >= 0.60 else None


@capture_internal_err
async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
) -> None:
    if not result:
        return

    forceplay = bool(forceplay)
    is_video = bool(video)

    if forceplay:
        await StreamController.force_stop_stream(chat_id)

    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        position = 0

        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(
                    search, videoid=search
                )
            except Exception:
                continue

            if str(duration_min) == "None":
                continue
            if duration_sec and duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if is_video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=is_video, videoid=vidid
                    )
                except Exception:
                    raise AssistantErr(_["play_14"])
                if not file_path:
                    raise AssistantErr(_["play_14"])

                await StreamController.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=is_video,
                    image=thumbnail,
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if is_video else "audio",
                    forceplay=forceplay,
                )
                img = thumbnail or await get_thumb(vidid, title=title)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:23],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        if count == 0:
            return
        link = await SAYABIN(msg)
        lines = msg.count("\n")
        car = os.linesep.join(msg.split(os.linesep)[:17]) if lines >= 17 else msg
        try:
            carbon = await Carbon.generate(car, randint(100, 10000000))
            playlist_photo = carbon
        except Exception:
            playlist_photo = config.PLAYLIST_IMG_URL
        upl = close_markup(_)
        final_position = len(db.get(chat_id) or []) - 1
        if final_position < 0:
            final_position = 0
        return await app.send_photo(
            original_chat_id,
            photo=playlist_photo,
            caption=_["play_21"].format(final_position, link),
            reply_markup=upl,
        )

    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]

        file_path, direct = None, None

        # YouTube Data API supplies search metadata only. Resolve audio from
        # Jamendo's official stream field; never extract YouTube media here.
        if not is_video:
            jamendo_track = await _jamendo_search_track(title)
            if not jamendo_track:
                raise AssistantErr("Can't find this song, try another song.")

            audio_url = jamendo_track.get("audio")
            artist = jamendo_track.get("artist_name") or "Unknown artist"
            license_url = jamendo_track.get("license_ccurl") or "Jamendo terms"
            duration_seconds = int(jamendo_track.get("duration") or 0)
            jamendo_duration = (
                f"{duration_seconds // 60}:{duration_seconds % 60:02d}"
                if duration_seconds else duration_min
            )
            jamendo_title = jamendo_track.get("name") or title
            jamendo_image = jamendo_track.get("image") or thumbnail or config.SOUNCLOUD_IMG_URL
            jamendo_share = jamendo_track.get("shareurl") or "https://www.jamendo.com/"

            if await is_active_chat(chat_id):
                await put_queue_index(
                    chat_id,
                    original_chat_id,
                    "index_url",
                    jamendo_title,
                    jamendo_duration,
                    user_name,
                    audio_url,
                    "audio",
                )
                position = len(db.get(chat_id)) - 1
                await app.send_message(
                    chat_id=original_chat_id,
                    text=_["queue_4"].format(
                        position, f"[JAMENDO] {jamendo_title}"[:27],
                        jamendo_duration, user_name
                    ),
                    reply_markup=InlineKeyboardMarkup(aq_markup(_, chat_id)),
                )
            else:
                if not forceplay:
                    db[chat_id] = []
                await StreamController.join_call(
                    chat_id, original_chat_id, audio_url, video=False
                )
                await put_queue_index(
                    chat_id,
                    original_chat_id,
                    "index_url",
                    jamendo_title,
                    jamendo_duration,
                    user_name,
                    audio_url,
                    "audio",
                    forceplay=forceplay,
                )
                caption = (
                    f"♫ {jamendo_title}\n"
                    f"Artist: {artist}\n"
                    f"Source: Jamendo\n"
                    f"Licence: {license_url}\n"
                    f"Track: {jamendo_share}\n"
                    f"Requested by: {user_name}"
                )
                run = await app.send_photo(
                    original_chat_id,
                    photo=jamendo_image,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            return


        # Preserve the existing video path; audio playback does not use YouTube extraction.
        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, video=True, videoid=vidid
            )
        except Exception as exc:
            from SayaMusic.logging import LOGGER as _LOGGER_FACTORY
            _LOGGER_FACTORY(__name__).warning(
                "YouTube video playback failed: %s", type(exc).__name__
            )

        if not file_path:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await StreamController.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=is_video,
                image=thumbnail,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            img = thumbnail or await get_thumb(vidid, title=title)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result.get("display_title") or result["title"]
        duration_min = result["duration_min"]
        source_label = result.get("display_source") or "SOUNDCLOUD"
        if not file_path:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, f"[{source_label}] {title}"[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await StreamController.join_call(chat_id, original_chat_id, file_path, video=False)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=result.get("display_thumb") or result.get("thumb") or config.SOUNCLOUD_IMG_URL,
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, f"[{source_label}] {title}"[:23], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        if not file_path:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await StreamController.join_call(chat_id, original_chat_id, file_path, video=is_video)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            if is_video:
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if is_video else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_1"].format(link, title[:23], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            if not file_path:
                raise AssistantErr(_["play_14"])

            await StreamController.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=is_video,
                image=thumbnail or None,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"


    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"

        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await mystic.edit_text(
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await StreamController.join_call(
                chat_id,
                original_chat_id,
                link,
                video=is_video,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()

# ZYN MUSIC
import asyncio
import random
import time
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.aio import VideosSearch

import config
from SayaMusic import app
from SayaMusic.misc import _boot_
from SayaMusic.plugins.sudo.sudoers import sudoers_list
from SayaMusic.utils import bot_sys_stats
from SayaMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    get_served_chats,
    get_served_users,
    get_monthly_active_users,
    get_start_video_id,
    set_start_video_id,
    clear_start_video_id,
    is_banned_user,
    is_on_off,
)
from SayaMusic.utils.decorators.language import LanguageStart
from SayaMusic.utils.formatters import get_readable_time
from SayaMusic.utils.inline.start import private_panel, start_panel
from SayaMusic.utils.inline.help import first_page
from config import BANNED_USERS, AYUV, HELP_IMG_URL, START_VIDS, STICKERS
from strings import get_string


@app.on_message(filters.command(["setstartvideo"]) & filters.private)
async def set_start_video_command(client, message: Message):
    if not message.from_user or message.from_user.id != config.OWNER_ID:
        return await message.reply_text("Only the configured bot owner can change the welcome video.")

    replied = message.reply_to_message
    video = getattr(replied, "video", None) if replied else None
    document = getattr(replied, "document", None) if replied else None
    file_id = video.file_id if video else (
        document.file_id
        if document and (document.mime_type or "").startswith("video/")
        else None
    )
    if not file_id:
        return await message.reply_text(
            "Reply to the uploaded MP4 video (send it as a video, not a compressed file if possible) "
            "with /setstartvideo to save it as the bot welcome video."
        )

    try:
        await set_start_video_id(file_id)
    except Exception as exc:
        print(f"Could not save start video setting: {type(exc).__name__}")
        return await message.reply_text("Couldn't save the welcome video. Check the database connection.")

    await message.reply_text("Premium Zayn × Alfiya welcome video saved. It will be used by /start.")


async def get_welcome_video():
    try:
        saved_video = await get_start_video_id()
    except Exception as exc:
        print(f"Could not read custom start video setting: {type(exc).__name__}")
        saved_video = None
    return saved_video or random.choice(START_VIDS)


async def send_welcome_video(message: Message, video, caption: str, reply_markup):
    try:
        return await message.reply_video(
            video,
            caption=caption,
            has_spoiler=True,
            reply_markup=reply_markup,
        )
    except Exception as video_error:
        print(f"Start welcome video failed: {type(video_error).__name__}")

    # If a saved Telegram file_id becomes unavailable, try the configured
    # HTTPS fallback before degrading to a text-only /start response.
    if video not in START_VIDS and START_VIDS:
        try:
            return await message.reply_video(
                random.choice(START_VIDS),
                caption=caption,
                has_spoiler=True,
                reply_markup=reply_markup,
            )
        except Exception as fallback_error:
            print(f"Fallback start video failed: {type(fallback_error).__name__}")

    return await message.reply_text(
        caption,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


@app.on_message(filters.command(["resetstartvideo"]) & filters.private)
async def reset_start_video_command(client, message: Message):
    if not message.from_user or message.from_user.id != config.OWNER_ID:
        return await message.reply_text("Only the configured bot owner can reset the welcome video.")
    try:
        await clear_start_video_id()
    except Exception as exc:
        print(f"Could not reset start video setting: {type(exc).__name__}")
        return await message.reply_text("Couldn't reset the welcome video. Check the database connection.")
    await message.reply_text("Custom welcome video cleared. /start will use the configured default URL.")




async def delete_sticker_after_delay(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    try:
        await add_served_user(message.from_user.id)
    except Exception:
        pass

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name.startswith("help"):
            keyboard = first_page(_)
            return await message.reply_photo(
                photo=HELP_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )

        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                username = f"@{message.from_user.username}" if message.from_user.username else "(none)"
                await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=(
                        f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n"
                        f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
                        f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username}"
                    ),
                )
            return

        if name.startswith("inf"):
            m = await message.reply_text("")
            try:
                vid_id = str(name).replace("info_", "", 1)
                query = f"https://www.youtube.com/watch?v={vid_id}"
                results = VideosSearch(query, limit=1)
                data = await results.next()
                result = (data.get("result") or [None])[0]
                if not result:
                    await m.edit_text("No results found.")
                    return

                title = result.get("title") or "Unknown"
                duration = result.get("duration") or "Unknown"
                views = (result.get("viewCount") or {}).get("short") or "Unknown"
                thumbnail = ((result.get("thumbnails") or [{}])[0].get("url") or "").split("?")[0]
                channellink = (result.get("channel") or {}).get("link") or "https://youtube.com"
                channel = (result.get("channel") or {}).get("name") or "Unknown"
                link = result.get("link") or query
                published = result.get("publishedTime") or "Unknown"

                searched_text = _["start_6"].format(title, duration, views, published, channellink, channel, app.mention)
                key = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text=_["S_B_6"], url=link),
                      InlineKeyboardButton(text=_["S_B_4"], url=config.SUPPORT_CHAT)]]
                )

                await m.delete()

                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail or HELP_IMG_URL,
                    caption=searched_text,
                    reply_markup=key,
                )

                if await is_on_off(2):
                    username = f"@{message.from_user.username}" if message.from_user.username else "(none)"
                    await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=(
                            f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n"
                            f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
                            f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username}"
                        ),
                    )
            except Exception as e:
                await m.edit_text(f"Error: {e}")
            return

    # Reply immediately so /start never appears completely silent while
    # database statistics, stickers, or welcome media are loading.
    status = await message.reply_text(
        "╭──────「 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 」\\n"
        "│ ✦ ᴡᴇʟᴄᴏᴍᴇ!\\n"
        "│ ⏳ ʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ᴍᴜsɪᴄ ᴘᴀɴᴇʟ...\\n"
        "╰────────────────"
    )

    try:
        out = private_panel(_)
        welcome_video = await get_welcome_video()

        try:
            sticker_message = await message.reply_sticker(
                sticker=random.choice(STICKERS)
            )
            asyncio.create_task(delete_sticker_after_delay(sticker_message, 2))
        except Exception as sticker_error:
            print(f"Start sticker skipped: {type(sticker_error).__name__}")

        # Statistics are optional; a database/statistics failure must not
        # prevent the welcome panel from being delivered.
        try:
            served_chats, served_users, (UP, CPU, RAM, DISK) = await asyncio.gather(
                get_served_chats(),
                get_served_users(),
                bot_sys_stats(),
            )
            monthly_active = await get_monthly_active_users()
            start_caption = random.choice(AYUV).format(
                message.from_user.mention, app.mention, UP, DISK, CPU, RAM,
                len(served_users), len(served_chats)
            )
            start_caption += (
                f"\\n\\n✦ ᴍᴏɴᴛʜʟʏ ᴀᴄᴛɪᴠᴇ ᴜsᴇʀs : {monthly_active:,}"
            )
        except Exception as stats_error:
            print(f"Start statistics unavailable: {type(stats_error).__name__}")
            start_caption = (
                f"Welcome {message.from_user.mention} to {app.mention}!\\n"
                "Choose an option below to explore the music bot."
            )

        sent = await send_welcome_video(
            message, welcome_video, start_caption, InlineKeyboardMarkup(out)
        )
        if sent:
            try:
                await status.delete()
            except Exception:
                pass
        else:
            await status.edit_text(start_caption, reply_markup=InlineKeyboardMarkup(out))

        if await is_on_off(2):
            username = f"@{message.from_user.username}" if message.from_user.username else "(none)"
            try:
                await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=(
                        f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\\n\\n"
                        f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\\n"
                        f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username}"
                    ),
                )
            except Exception as log_error:
                print(f"Start logger message skipped: {type(log_error).__name__}")
    except Exception as start_error:
        print(f"Private /start handler failed: {type(start_error).__name__}: {start_error}")
        try:
            await status.edit_text(
                "Welcome to 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 🎧\\n"
                "The full welcome panel could not load. Please try /start again.",
                reply_markup=InlineKeyboardMarkup(private_panel(_)),
            )
        except Exception:
            pass


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    welcome_video = await get_welcome_video()
    uptime = int(time.time() - _boot_)
    group_start_caption = _["start_1"].format(app.mention, get_readable_time(uptime))
    await send_welcome_video(
        message, welcome_video, group_start_caption, InlineKeyboardMarkup(out)
    )
    return await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except Exception:
                    pass

            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                welcome_video = await get_welcome_video()
                await send_welcome_video(
                    message,
                    welcome_video,
                    _["start_3"].format(
                        message.from_user.mention,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    InlineKeyboardMarkup(out),
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()

        except Exception as ex:
            print(ex)

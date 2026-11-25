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
    if not video:
        return await message.reply_text(
            "Reply to the uploaded MP4 video with /setstartvideo to save it as the bot welcome video."
        )

    try:
        await set_start_video_id(video.file_id)
    except Exception as exc:
        print(f"Could not save start video setting: {type(exc).__name__}")
        return await message.reply_text("Couldn't save the welcome video. Check the database connection.")

    await message.reply_text("Premium Zayn × Alfiya welcome video saved. It will be used by /start.")


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

    out = private_panel(_)
    welcome_video = await get_start_video_id() or random.choice(START_VIDS)
    sticker_message = await message.reply_sticker(sticker=random.choice(STICKERS))
    asyncio.create_task(delete_sticker_after_delay(sticker_message, 2))

    served_chats_coro = get_served_chats()
    served_users_coro = get_served_users()
    stats_coro = bot_sys_stats()
    served_chats, served_users, (UP, CPU, RAM, DISK) = await asyncio.gather(
        served_chats_coro, served_users_coro, stats_coro
    )

    monthly_active = await get_monthly_active_users()
    start_caption = random.choice(AYUV).format(
        message.from_user.mention, app.mention, UP, DISK, CPU, RAM, len(served_users), len(served_chats)
    )
    start_caption += f"\n\n✦ ᴍᴏɴᴛʜʟʏ ᴀᴄᴛɪᴠᴇ ᴜsᴇʀs : {monthly_active:,}"

    try:
        await message.reply_video(
            welcome_video,
            caption=start_caption,
            has_spoiler=True,
            reply_markup=InlineKeyboardMarkup(out),
        )
    except Exception as video_error:
        # Keep /start usable if the configured welcome video host is unavailable.
        print(f"Start welcome video failed: {type(video_error).__name__}")
        await message.reply_text(
            start_caption,
            reply_markup=InlineKeyboardMarkup(out),
            disable_web_page_preview=True,
        )

    if await is_on_off(2):
        username = f"@{message.from_user.username}" if message.from_user.username else "(none)"
        await app.send_message(
            chat_id=config.LOGGER_ID,
            text=(
                f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n"
                f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
                f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username}"
            ),
        )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    welcome_video = await get_start_video_id() or random.choice(START_VIDS)
    uptime = int(time.time() - _boot_)
    group_start_caption = _["start_1"].format(app.mention, get_readable_time(uptime))
    try:
        await message.reply_video(
            welcome_video,
            caption=group_start_caption,
            has_spoiler=True,
            reply_markup=InlineKeyboardMarkup(out),
        )
    except Exception as video_error:
        print(f"Group start welcome video failed: {type(video_error).__name__}")
        await message.reply_text(
            group_start_caption,
            reply_markup=InlineKeyboardMarkup(out),
            disable_web_page_preview=True,
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
                welcome_video = await get_start_video_id() or random.choice(START_VIDS)
                await message.reply_video(
                    welcome_video,
                    caption=_["start_3"].format(
                        message.from_user.mention,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    has_spoiler=True,
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()

        except Exception as ex:
            print(ex)

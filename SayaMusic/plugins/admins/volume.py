# ZYN MUSIC
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ChatMemberStatus

from config import BANNED_USERS
from SayaMusic import app
from SayaMusic.core.call import StreamController
from SayaMusic.utils import AdminRightsCheck
from SayaMusic.utils.database import is_active_chat
from SayaMusic.utils.decorators.language import languageCB
from SayaMusic.utils.inline import close_markup
from SayaMusic.utils.group_admin import is_real_group_admin


VOLUME_LEVELS = (50, 75, 100, 125, 150, 175, 200)


def volume_markup(chat_id: int) -> InlineKeyboardMarkup:
    rows = []
    for start in range(0, len(VOLUME_LEVELS), 3):
        rows.append([
            InlineKeyboardButton(
                text=f"{level}%",
                callback_data=f"ZynVolume {chat_id}|{level}",
            )
            for level in VOLUME_LEVELS[start:start + 3]
        ])
    rows.append([InlineKeyboardButton(text="Close", callback_data="close")])
    return InlineKeyboardMarkup(rows)


@app.on_message(filters.command(["volume", "vol"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def volume_command(_, message: Message, language, chat_id: int):
    if not await is_real_group_admin(_, chat_id, message.from_user.id):
        return await message.reply_text("Only admins of this group can control playback.")
    if not await is_active_chat(chat_id):
        return await message.reply_text("Nothing is playing right now.")
    return await message.reply_text(
        "🎚 Choose playback volume (50%–200%):",
        reply_markup=volume_markup(chat_id),
    )


@app.on_callback_query(filters.regex(r"^ZynVolume ") & ~BANNED_USERS)
@languageCB
async def volume_callback(_, query, language):
    try:
        payload = query.data.split(None, 1)[1]
        raw_chat, raw_volume = payload.split("|", 1)
        chat_id, volume = int(raw_chat), int(raw_volume)
    except (IndexError, TypeError, ValueError):
        return await query.answer("Invalid volume control.", show_alert=True)

    if not query.message or query.message.chat.id != chat_id:
        return await query.answer("This control belongs to another group.", show_alert=True)
    if volume not in VOLUME_LEVELS:
        return await query.answer("Unsupported volume level.", show_alert=True)
    if not await is_active_chat(chat_id):
        return await query.answer("Nothing is playing right now.", show_alert=True)

    try:
        member = await app.get_chat_member(chat_id, query.from_user.id)
    except Exception:
        return await query.answer("Unable to verify your group permissions.", show_alert=True)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await query.answer("Only group admins can change volume.", show_alert=True)

    try:
        await StreamController.set_volume(chat_id, volume)
    except Exception:
        return await query.answer("Couldn't change volume. Check assistant permissions and active call.", show_alert=True)

    await query.answer(f"Volume set to {volume}%.")
    try:
        await query.message.edit_text(
            f"🔊 Playback volume: **{volume}%**",
            reply_markup=close_markup(language),
        )
    except Exception:
        pass

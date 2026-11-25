# ZYN MUSIC
from pyrogram import filters
from pyrogram.types import Message

from SayaMusic import app
from SayaMusic.utils.group_admin import is_real_group_admin
from SayaMusic.utils.database import is_group_control_mode, set_group_control_mode
from config import BANNED_USERS


@app.on_message(filters.command(["groupmode"]) & filters.group & ~BANNED_USERS)
async def group_control_mode(_, message: Message):
    if not message.from_user:
        return await message.reply_text("Only a group admin can change playback control mode.")
    if not await is_real_group_admin(_, message.chat.id, message.from_user.id):
        return await message.reply_text("Only actual admins of this group can change /groupmode.")

    if len(message.command) != 2 or message.command[1].lower() not in {"on", "off", "status"}:
        current = await is_group_control_mode(message.chat.id)
        state = "ON — members can use playback controls" if current else "OFF — admins only"
        return await message.reply_text(
            "**Group playback control mode**\n"
            f"Current: {state}\n\n"
            "/groupmode on — allow members to pause, resume, skip, loop, shuffle, seek, volume and speed\n"
            "/groupmode off — admins only\n"
            "**Stop/End always remains admin-only.**"
        )

    action = message.command[1].lower()
    if action == "status":
        enabled = await is_group_control_mode(message.chat.id)
    else:
        enabled = action == "on"
        await set_group_control_mode(message.chat.id, enabled)

    if enabled:
        return await message.reply_text(
            "✅ Group mode is ON. Members can use normal playback controls. "
            "Only actual group admins can Stop/End the stream."
        )
    return await message.reply_text("🔒 Group mode is OFF. Playback controls are admins-only.")

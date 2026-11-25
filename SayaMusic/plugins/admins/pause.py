# Saya Music
from pyrogram import filters
from pyrogram.types import Message

from SayaMusic import app
from SayaMusic.core.call import StreamController
from SayaMusic.utils.database import is_music_playing, music_off
from SayaMusic.utils.decorators import AdminRightsCheck
from SayaMusic.utils.inline import close_markup
from SayaMusic.utils.group_admin import is_real_group_admin
from config import BANNED_USERS


@app.on_message(filters.command(["pause", "cpause"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def pause_admin(cli, message: Message, _, chat_id):
    if not await is_real_group_admin(cli, chat_id, message.from_user.id):
        return await message.reply_text("Only admins of this group can control playback.")
    if not await is_music_playing(chat_id):
        return await message.reply_text(_["admin_1"])
    await music_off(chat_id)
    await StreamController.pause_stream(chat_id)
    await message.reply_text(
        _["admin_2"].format(message.from_user.mention), reply_markup=close_markup(_)
    )

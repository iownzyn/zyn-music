# Saya Music
from pyrogram import filters
from pyrogram.types import Message

from SayaMusic import app
from SayaMusic.core.call import StreamController
from SayaMusic.utils.database import set_loop
from SayaMusic.utils.decorators import AdminRightsCheck
from SayaMusic.utils.inline import close_markup
from SayaMusic.utils.group_admin import is_real_group_admin
from config import BANNED_USERS


@app.on_message(
    filters.command(["end"], prefixes=["/", "!"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_music(cli, message: Message, _, chat_id):
    if not await is_real_group_admin(cli, chat_id, message.from_user.id):
        return await message.reply_text("Only admins of this group can control playback.")
    if not len(message.command) == 1:
        return
    await StreamController.stop_stream(chat_id)
    await set_loop(chat_id, 0)
    await message.reply_text(
        _["admin_5"].format(message.from_user.mention), reply_markup=close_markup(_)
    )

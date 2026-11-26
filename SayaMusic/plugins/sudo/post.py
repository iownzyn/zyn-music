# Saya Music
import asyncio

from pyrogram import filters
from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked, InputUserDeactivated, ChatWriteForbidden
from SayaMusic import app
from config import OWNER_ID
from SayaMusic.utils.database import get_served_users, get_served_chats

destination_group_id = -1002076109983

@app.on_message(filters.command(["post"], prefixes=["/", "."]) & filters.user(OWNER_ID))
async def copy_messages(_, message):

    if message.reply_to_message:

        await message.reply_to_message.copy(destination_group_id)
        await message.reply("ᴘᴏsᴛ sᴜᴄᴄᴇssғᴜʟ ᴅᴏɴᴇ ")


@app.on_message(filters.command(["broadcast", "bcast"], prefixes=["/", "."]) & filters.user(OWNER_ID))
async def broadcast_message(client, message):
    """Copy an owner's replied message to users who started the bot and served groups."""
    if not message.reply_to_message:
        return await message.reply_text(
            "Reply to the message/media you want to broadcast, then send /broadcast."
        )

    status = await message.reply_text("Broadcast started…")
    users = await get_served_users()
    chats = await get_served_chats()
    targets = [item["user_id"] for item in users if item.get("user_id")]
    targets += [item["chat_id"] for item in chats if item.get("chat_id")]

    sent = failed = 0
    blocked = 0
    for target in dict.fromkeys(targets):
        try:
            await message.reply_to_message.copy(chat_id=target)
            sent += 1
        except FloodWait as exc:
            await asyncio.sleep(exc.value)
            try:
                await message.reply_to_message.copy(chat_id=target)
                sent += 1
            except Exception:
                failed += 1
        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid, ChatWriteForbidden):
            failed += 1
            blocked += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.06)

    await status.edit_text(
        "Broadcast completed.\n\n"
        f"• Delivered: {sent}\n"
        f"• Failed: {failed}\n"
        f"• Blocked/unreachable: {blocked}\n"
        f"• Total targets: {len(set(targets))}"
    )

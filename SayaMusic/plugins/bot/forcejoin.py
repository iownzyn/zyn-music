# ZYN MUSIC mandatory community membership gate
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config
from SayaMusic import app

REQUIRED_CHATS = (
    ("@zynchatgc", config.SUPPORT_CHAT, "Support Group"),
    ("@zynmusicupdates", config.SUPPORT_CHANNEL, "Updates Channel"),
)


def force_join_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Join Support Group", url=config.SUPPORT_CHAT),
                InlineKeyboardButton("Join Channel", url=config.SUPPORT_CHANNEL),
            ],
            [InlineKeyboardButton("I Joined • Verify", callback_data="forcejoin_verify")],
        ]
    )


async def check_force_join(user_id: int):
    missing = []
    for chat, _, label in REQUIRED_CHATS:
        try:
            member = await app.get_chat_member(chat, user_id)
            status = getattr(member, "status", None)
            is_member = status in (
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            )
            if status == ChatMemberStatus.RESTRICTED:
                is_member = bool(getattr(member, "is_member", False))
            if not is_member:
                missing.append(label)
        except Exception:
            missing.append(label)
    return missing


async def require_force_join(message):
    missing = await check_force_join(message.from_user.id)
    if not missing:
        return True
    await message.reply_text(
        "🎧 **𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 — Join Check**\n\n"
        "Bot use karne se pehle Support Group aur Updates Channel join karein. "
        "Dono join karne ke baad **I Joined • Verify** dabayein.\n\n"
        "Pending: " + ", ".join(missing),
        reply_markup=force_join_markup(),
        disable_web_page_preview=True,
    )
    return False


@app.on_callback_query(filters.regex("^forcejoin_verify$"))
async def forcejoin_verify_callback(client, query):
    missing = await check_force_join(query.from_user.id)
    if missing:
        await query.answer(
            "Abhi join pending hai: " + ", ".join(missing),
            show_alert=True,
        )
        return
    await query.answer("Verified! ZYN MUSIC is unlocked.", show_alert=True)
    try:
        await query.message.edit_text(
            "✅ **Membership verified!**\n\nAb /start karein ya apne group mein /play use karein.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Open Bot", url=f"https://t.me/{app.username}?start=home")]]
            ),
        )
    except Exception:
        pass

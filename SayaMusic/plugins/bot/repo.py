# ZYN MUSIC
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from SayaMusic import app
import config
from config import BOT_USERNAME

repo_caption = """**
 ᴄʟᴏɴᴇ ᴀɴᴅ ᴅᴇᴘʟᴏʏ – 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 🎧 

 ᴅᴇᴘʟᴏʏ ᴇᴀsɪʟʏ ᴏɴ Render ᴡɪᴛʜ Docker
 ᴄʟᴇᴀɴ 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 ʙʀᴀɴᴅɪɴɢ
 ᴅᴏᴄᴋᴇʀ, ᴘʀᴏᴄꜰɪʟᴇ, ᴀɴᴅ Render ᴇɴᴠ ᴠᴀʀs ʀᴇᴀᴅʏ
 ʀᴜɴ 24/7 ʟᴀɢ ꜰʀᴇᴇ

ɪꜰ ʏᴏᴜ ꜰᴀᴄᴇ ᴀɴʏ ᴘʀᴏʙʟᴇᴍ, ᴏᴘᴇɴ ᴀɴ ɪꜱꜱᴜᴇ ᴏʀ ᴄʜᴇᴄᴋ ꜱᴜᴘᴘᴏʀᴛ
**"""

@app.on_message(filters.command("repo"))
async def show_repo(_, msg):
    buttons = [
        [InlineKeyboardButton(" ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ ", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [
            InlineKeyboardButton(" ᴏᴡɴᴇʀ", url=f"https://github.com/{config.OWNER_USERNAME}"),
            InlineKeyboardButton(" ꜱᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT)
        ],
        [
            InlineKeyboardButton(" Render", url="https://render.com/"),
            InlineKeyboardButton(" ɢɪᴛʜᴜʙ", url=config.UPSTREAM_REPO)
        ]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    try:  
        await msg.reply_photo(
            photo=config.HELP_IMG_URL,
            caption=repo_caption,
            reply_markup=reply_markup
        )
    except:
        pass

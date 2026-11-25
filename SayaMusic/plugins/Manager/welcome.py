# ZYN MUSIC
import os
import asyncio
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, enums
from pyrogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import TopicClosed, PeerIdInvalid, ChannelPrivate, SlowmodeWait
from SayaMusic import app
from SayaMusic.mongo.welcomedb import is_on, set_state, bump, cool, auto_on

BG_PATH = "SayaMusic/assets/saya/welcome.png"
FALLBACK_PIC = "SayaMusic/assets/upic.png"
FONT_PATH = "SayaMusic/assets/saya/Arimo.ttf"

BTN_VIEW = "View Member"
BTN_HELP = "Help"
BTN_ADD = "Add Bot"

CAPTION_TXT = """
**──── 𝐀𝐋𝐅𝐈𝐘𝐀 × 𝐙𝐀𝐘𝐍 ────
ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂
{chat_title}
▰▰▰▰▰▰▰▰▰▰▰▰▰
 Nᴀᴍᴇ  {mention}
 Iᴅ  `{uid}`
 Usᴇʀɴᴀᴍᴇ  @{uname}
 Tᴏᴛᴀʟ Mᴇᴍʙᴇʀs  {count}
▰▰▰▰▰▰▰▰▰▰▰▰▰**
**──────────**
"""

JOIN_THRESHOLD = 20
TIME_WINDOW = 10
COOL_MINUTES = 5
WELCOME_LIMIT = 5

last_messages = {}


async def cleanup(path):
    """Remove generated/downloaded welcome media without touching bundled assets."""
    if not path or not os.path.exists(path):
        return
    try:
        resolved = os.path.abspath(path)
        assets_dir = os.path.abspath("SayaMusic/assets")
        if os.path.commonpath((resolved, assets_dir)) == assets_dir:
            return
        os.remove(resolved)
    except (OSError, ValueError):
        pass


@lru_cache(maxsize=1)
def cached_bg():
    # The repository's old welcome.png placeholder is empty; create a
    # deterministic branded canvas when the bundled artwork is unavailable.
    try:
        if os.path.exists(BG_PATH) and os.path.getsize(BG_PATH) > 0:
            return Image.open(BG_PATH).convert("RGBA")
    except OSError:
        pass
    image = Image.new("RGBA", (1280, 720), (28, 35, 49, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, 1252, 692), radius=42,
                           fill=(39, 50, 68, 255), outline=(190, 160, 150, 255), width=4)
    draw.ellipse((790, 95, 1160, 465), fill=(65, 76, 94, 255), outline=(210, 185, 170, 255), width=5)
    draw.text((90, 95), "WELCOME TO", fill=(238, 228, 220, 255), font=ImageFont.truetype(FONT_PATH, 42))
    draw.text((90, 165), "ZYN MUSIC", fill=(255, 245, 235, 255), font=ImageFont.truetype(FONT_PATH, 78))
    draw.text((90, 590), "ALFIYA  ×  ZAYN", fill=(225, 190, 180, 255), font=ImageFont.truetype(FONT_PATH, 34))
    return image

@lru_cache(maxsize=2)
def cached_font(size=65):
    return ImageFont.truetype(FONT_PATH, size)

def circle(im, size=(835, 839)):
    im = im.resize(size, Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, *size), fill=255)
    im.putalpha(mask)
    return im

def build_pic(av, fn, uid, un):
    os.makedirs("downloads", exist_ok=True)
    bg = cached_bg().copy()
    avatar = circle(Image.open(av), size=(330, 330))
    bg.paste(avatar, (820, 160), avatar)
    d = ImageDraw.Draw(bg)
    f = cached_font(42)
    d.text((90, 340), fn[:24], fill=(242, 242, 242), font=f)
    d.text((90, 415), f"ID  {uid}", fill=(215, 210, 205), font=ImageFont.truetype(FONT_PATH, 28))
    d.text((90, 475), f"@{un[:24]}", fill=(215, 210, 205), font=ImageFont.truetype(FONT_PATH, 28))
    path = f"downloads/welcome_{uid}.png"
    bg.save(path)
    return path

async def safe_send(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except:
        return None

@app.on_message(filters.command("welcome") & filters.group)
async def toggle(client, m: Message):
    if len(m.command) != 2:
        return await m.reply_text("**Usage:**\n⦿/welcome [on|off]\n ZYN MUSIC Special Welcome.....")
    user_id = m.from_user.id if m.from_user else (m.sender_chat.id if m.sender_chat else None)
    if not user_id:
        return
    try:
        u = await client.get_chat_member(m.chat.id, user_id)
    except:
        return
    if u.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await m.reply_text("**sᴏʀʀʏ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴄʜᴀɴɢᴇ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ sᴛᴀᴛᴜs!**")
    flag = m.command[1].lower()
    if flag not in ("on", "off"):
        return await m.reply_text("**Usage:**\n⦿/welcome [on|off]\n ZYN MUSIC Special Welcome.....")
    cur = await is_on(m.chat.id)
    if flag == "off" and not cur:
        return await m.reply_text("**ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ!**")
    if flag == "on" and cur:
        return await m.reply_text("**ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴀʟʀᴇᴀᴅʏ ᴇɴᴀʙʟᴇᴅ!**")
    await set_state(m.chat.id, flag)
    await m.reply_text(f"**{'ᴇɴᴀʙʟᴇᴅ' if flag == 'on' else 'ᴅɪsᴀʙʟᴇᴅ'} ᴡᴇʟᴄᴏᴍᴇ ɪɴ {m.chat.title}**")

@app.on_chat_member_updated(filters.group, group=-3)
async def welcome(client, update: ChatMemberUpdated):
    new = update.new_chat_member
    old = update.old_chat_member
    cid = update.chat.id

    if not new or new.status != enums.ChatMemberStatus.MEMBER:
        return
    if old and old.status == enums.ChatMemberStatus.MEMBER:
        return

    if not hasattr(client, "cached_me"):
        try:
            client.cached_me = await client.get_me()
        except:
            return
    me = client.cached_me

    try:
        await client.get_chat_member(cid, me.id)
    except:
        return

    if not await is_on(cid):
        if await auto_on(cid):
            await safe_send(client.send_message, cid, "**ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇs ʀᴇ-ᴇɴᴀʙʟᴇᴅ.**")
        else:
            return

    burst = await bump(cid, TIME_WINDOW)
    if burst >= JOIN_THRESHOLD:
        minutes = min(60, COOL_MINUTES + max(0, burst - JOIN_THRESHOLD) * 2)
        await cool(cid, minutes)
        await safe_send(client.send_message, cid, f"**ᴍᴀssɪᴠᴇ ᴊᴏɪɴ ᴅᴇᴛᴇᴄᴛᴇᴅ (x{burst}). ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇs ᴅɪsᴀʙʟᴇᴅ ғᴏʀ {minutes} ᴍɪɴᴜᴛᴇs.**")
        return

    user = new.user
    file_id = None
    if user.photo and hasattr(user.photo, "big_file_id"):
        file_id = user.photo.big_file_id

    avatar = await safe_send(client.download_media, file_id, file_name=f"downloads/pp_{user.id}.png") if file_id else None
    if not avatar:
        avatar = FALLBACK_PIC

    try:
        img = build_pic(avatar, user.first_name, user.id, user.username or "No Username")
    except Exception:
        # Keep welcomes working even if the optional image template/font is missing.
        img = avatar if avatar and os.path.exists(avatar) else None

    members = await safe_send(client.get_chat_members_count, cid) or "?"

    caption = CAPTION_TXT.format(
        chat_title=update.chat.title,
        mention=user.mention,
        uid=user.id,
        uname=user.username or "No Username",
        count=members
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(BTN_VIEW, url=f"tg://openmessage?user_id={user.id}"),
            InlineKeyboardButton(BTN_HELP, callback_data="open_help"),
        ],
        [InlineKeyboardButton(BTN_ADD, url=f"https://t.me/{me.username}?startgroup=true")],
    ])
    sent = None
    if img:
        sent = await safe_send(
            client.send_photo, cid, img, caption=caption, reply_markup=keyboard
        )
    if not sent:
        sent = await safe_send(
            client.send_message, cid, caption, reply_markup=keyboard
        )

    if sent:
        last_messages.setdefault(cid, []).append(sent)
        if len(last_messages[cid]) > WELCOME_LIMIT:
            old_msg = last_messages[cid].pop(0)
            if old_msg:
                await safe_send(old_msg.delete)

    asyncio.create_task(cleanup(avatar))
    asyncio.create_task(cleanup(img))


@app.on_chat_member_updated(filters.group, group=-2)
async def goodbye(client, update: ChatMemberUpdated):
    """Send a compact goodbye when a regular member leaves or is removed."""
    new = update.new_chat_member
    old = update.old_chat_member
    if not new or not old:
        return
    if old.status not in (enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.RESTRICTED):
        return
    if new.status not in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED):
        return

    user = new.user
    if not user or user.is_bot or not await is_on(update.chat.id):
        return

    caption = (
        f"╭──────「 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 」\n"
        f"│ 👋 ɢᴏᴏᴅʙʏᴇ, {user.mention}\n"
        f"│\n"
        f"│ ᴡᴇ ʜᴏᴘᴇ ᴛᴏ sᴇᴇ ʏᴏᴜ ᴀɢᴀɪɴ!\n"
        f"╰────────────────"
    )
    photo_path = None
    try:
        if user.photo and hasattr(user.photo, "big_file_id"):
            os.makedirs("downloads", exist_ok=True)
            photo_path = await safe_send(
                client.download_media,
                user.photo.big_file_id,
                file_name=f"downloads/goodbye_{user.id}.jpg",
            )
    except Exception:
        photo_path = None

    if photo_path and os.path.exists(photo_path):
        sent = await safe_send(
            client.send_photo, update.chat.id, photo_path, caption=caption
        )
        if sent:
            asyncio.create_task(cleanup(photo_path))
            return

    await safe_send(client.send_message, update.chat.id, caption)

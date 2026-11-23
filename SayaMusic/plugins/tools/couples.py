# ZYN MUSIC
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from pyrogram import errors, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from SayaMusic import app
from SayaMusic.core.dir import COUPLE_DIR
from SayaMusic.mongo.couples_db import get_couple, save_couple


ASSETS = Path("SayaMusic/assets")
FALLBACK = ASSETS / "upic.png"
COUPLE_TEMPLATE = ASSETS / "saya/couple.png"
COUPLE_FONT = ASSETS / "saya/Arimo.ttf"
OUT_DIR = Path(COUPLE_DIR)


def today() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def tomorrow() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")


def circular(path: str | Path) -> Image.Image:
    try:
        img = Image.open(path).convert("RGBA").resize((486, 486))
    except (FileNotFoundError, UnidentifiedImageError, OSError):
        img = Image.open(FALLBACK).convert("RGBA").resize((486, 486))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + img.size, fill=255)
    img.putalpha(mask)
    return img


def couple_canvas() -> Image.Image:
    """Load a valid template, or build a complete fallback when the PNG is empty."""
    try:
        with Image.open(COUPLE_TEMPLATE) as source:
            source.verify()
        with Image.open(COUPLE_TEMPLATE) as source:
            return source.convert("RGBA")
    except (FileNotFoundError, UnidentifiedImageError, OSError):
        width, height = 2300, 1400
        base = Image.new("RGBA", (width, height), (18, 24, 48, 255))
        pixels = base.load()
        for y in range(height):
            t = y / max(1, height - 1)
            color = (
                int(36 + 92 * t),
                int(24 + 22 * t),
                int(68 + 66 * t),
                255,
            )
            for x in range(width):
                pixels[x, y] = color

        draw = ImageDraw.Draw(base)
        draw.rounded_rectangle((90, 70, width - 90, height - 70), radius=70,
                               outline=(255, 220, 238, 210), width=8)
        draw.ellipse((1020, 430, 1280, 690), outline=(255, 205, 230, 150), width=8)
        try:
            font = ImageFont.truetype(str(COUPLE_FONT), 112)
            small = ImageFont.truetype(str(COUPLE_FONT), 42)
        except OSError:
            font = ImageFont.load_default()
            small = ImageFont.load_default()

        title = "Alfiya  ♥  Zayn"
        box = draw.textbbox((0, 0), title, font=font, stroke_width=2)
        title_w = box[2] - box[0]
        draw.text(((width - title_w) / 2, 185), title, font=font,
                  fill=(255, 242, 248, 255), stroke_width=2,
                  stroke_fill=(110, 45, 90, 255))
        subtitle = "A LITTLE MATCH MADE IN MUSIC"
        box = draw.textbbox((0, 0), subtitle, font=small)
        draw.text(((width - (box[2] - box[0])) / 2, 330), subtitle,
                  font=small, fill=(255, 220, 238, 240))
        return base


async def safe_get_user(uid: int):
    try:
        return await app.get_users(uid)
    except (errors.PeerIdInvalid, errors.UserNotParticipant):
        return None


async def safe_photo(uid: int, name: str) -> Path:
    try:
        chat = await app.get_chat(uid)
        if chat.photo and chat.photo.big_file_id:
            path = await app.download_media(chat.photo.big_file_id, file_name=OUT_DIR / name)
            return Path(path) if path else FALLBACK
    except Exception:
        pass
    return FALLBACK


async def generate_image(chat_id: int, uid1: int, uid2: int, date: str) -> str:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = couple_canvas()
    p1 = await safe_photo(uid1, "pfp1.png")
    p2 = await safe_photo(uid2, "pfp2.png")

    a1 = circular(p1)
    a2 = circular(p2)
    base.paste(a1, (410, 500), a1)
    base.paste(a2, (1395, 500), a2)

    out_path = OUT_DIR / f"couple_{chat_id}_{date.replace('/','-')}.png"
    base.save(out_path, format="PNG")

    for pf in (p1, p2):
        try:
            if pf != FALLBACK and pf.exists() and pf.parent == OUT_DIR:
                pf.unlink()
        except OSError:
            pass

    return str(out_path)


@app.on_message(filters.command("couple"))
async def couples_handler(_, message: Message):
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋs ɪɴ ɢʀᴏᴜᴘs.**")

    wait = await message.reply("**Creating today's couple card...**")
    cid = message.chat.id
    date = today()

    record = await get_couple(cid, date)
    if record:
        uid1, uid2, img_path = record["user1"], record["user2"], record["img"]
        user1 = await safe_get_user(uid1)
        user2 = await safe_get_user(uid2)
        if not (user1 and user2) or not img_path or not Path(img_path).exists():
            record = None

    if not record:
        members = [
            m.user.id async for m in app.get_chat_members(cid, limit=250)
            if m.user and not m.user.is_bot
        ]
        if len(members) < 2:
            await wait.edit("**ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴜsᴇʀs ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ.**")
            return

        for _attempt in range(5):
            uid1, uid2 = random.sample(members, 2)
            user1 = await safe_get_user(uid1)
            user2 = await safe_get_user(uid2)
            if user1 and user2:
                break
        else:
            await wait.edit("**ᴄᴏᴜʟᴅ ɴᴏᴛ ꜰɪɴᴅ ᴠᴀʟɪᴅ ᴍᴇᴍʙᴇʀꜱ.**")
            return

        img_path = await generate_image(cid, uid1, uid2, date)
        await save_couple(cid, date, {"user1": uid1, "user2": uid2}, img_path)

    caption = (
        " **ᴄᴏᴜᴘʟᴇ ᴏꜰ ᴛʜᴇ ᴅᴀʏ!** \n\n"
        "╔════════════╗\n"
        f" **ᴛᴏᴅᴀʏ'ꜱ ᴄᴏᴜᴘʟᴇ:**\n⤷ {user1.mention}  {user2.mention}\n"
        "╚════════════╝\n\n"
        f" **ɴᴇxᴛ ꜱᴇʟᴇᴄᴛɪᴏɴ:** `{tomorrow()}`\n\n"
        " **ᴛᴀɢ ʏᴏᴜʀ ᴄʀᴜꜱʜ — ʏᴏᴜ ᴍɪɢʜᴛ ʙᴇ ɴᴇxᴛ!** "
    )

    try:
        await message.reply_photo(img_path, caption=caption)
        await wait.delete()
    except Exception as exc:
        await wait.edit(f"Could not send the couple card: {type(exc).__name__}")

# ZYN MUSIC
import os
import re
import random
import uuid
import time
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from config import YOUTUBE_IMG_URL
from SayaMusic.core.dir import CACHE_DIR


PANEL_W, PANEL_H = 763, 545
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 88
TRANSPARENCY = 170
INNER_OFFSET = 36

THUMB_W, THUMB_H = 542, 273
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + INNER_OFFSET

TITLE_X = 377
META_X = 377
TITLE_Y = THUMB_Y + THUMB_H + 10
META_Y = TITLE_Y + 45

BAR_X, BAR_Y = 388, META_Y + 45
BAR_RED_LEN = 280
BAR_TOTAL_LEN = 480

ICONS_W, ICONS_H = 415, 45
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 48

MAX_TITLE_WIDTH = 580

def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis

def _draw_original_couple_scene() -> Image.Image:
    """Create a fresh, clean storybook/anime-inspired couple card without neon."""
    palettes = [
        ((244, 232, 222), (224, 205, 194), (105, 79, 83), (70, 80, 93)),
        ((229, 235, 225), (201, 218, 204), (83, 105, 92), (104, 83, 100)),
        ((234, 228, 240), (211, 201, 226), (79, 73, 105), (114, 83, 92)),
        ((241, 232, 213), (226, 212, 183), (91, 79, 65), (87, 99, 112)),
        ((224, 233, 239), (196, 214, 224), (76, 88, 104), (115, 82, 88)),
        ((242, 225, 229), (225, 197, 204), (91, 72, 82), (71, 89, 98)),
    ]
    bgc, accent, hair_a, hair_b = random.choice(palettes)
    skin_a = random.choice([(244, 207, 185), (232, 190, 169), (249, 218, 196)])
    skin_b = random.choice([(239, 199, 178), (224, 181, 161), (247, 211, 190)])
    cloth_a = random.choice([(91, 111, 124), (137, 102, 105), (110, 119, 95), (126, 105, 137)])
    cloth_b = random.choice([(183, 143, 132), (104, 126, 119), (151, 131, 104), (121, 111, 139)])

    image = Image.new("RGB", (1280, 720), bgc)
    d = ImageDraw.Draw(image)
    # Soft paper-like backdrop with a warm oval vignette and quiet botanical accents.
    d.ellipse((120, 25, 1160, 820), fill=accent)
    d.ellipse((190, 60, 1090, 760), fill=bgc)
    for _ in range(22):
        x, y = random.randint(45, 1235), random.randint(35, 650)
        r = random.randint(3, 9)
        color = random.choice([(255, 250, 242), (255, 242, 235), (214, 177, 169)])
        d.ellipse((x-r, y-r, x+r, y+r), fill=color)
    # A few delicate leaves/flowers keep the frame Pinterest-like, not neon.
    for x, y in [(150, 520), (1110, 485), (250, 180), (1010, 160)]:
        d.arc((x-42, y-65, x+42, y+65), 210, 330, fill=(132, 147, 124), width=4)
        for dx, dy in [(-18, -18), (18, 4), (-8, 30)]:
            d.ellipse((x+dx-12, y+dy-7, x+dx+12, y+dy+7), fill=(173, 188, 157))

    # Shoulders and clothes: two figures leaning toward each other.
    d.ellipse((245, 405, 695, 900), fill=cloth_a)
    d.ellipse((585, 405, 1035, 900), fill=cloth_b)
    d.rounded_rectangle((440, 370, 840, 720), radius=120, fill=accent)

    # Neck and faces.
    d.rounded_rectangle((430, 285, 540, 455), radius=45, fill=skin_a)
    d.rounded_rectangle((740, 285, 850, 455), radius=45, fill=skin_b)
    d.ellipse((350, 105, 615, 430), fill=skin_a, outline=(105, 80, 76), width=5)
    d.ellipse((665, 105, 930, 430), fill=skin_b, outline=(105, 80, 76), width=5)

    # Hair silhouettes and random fringe shapes.
    d.pieslice((325, 65, 640, 430), 180, 360, fill=hair_a)
    d.polygon([(345, 205), (365, 85), (430, 48), (515, 62), (612, 145), (588, 310),
               (552, 245), (520, 190), (485, 265), (455, 188), (410, 270), (380, 230)],
              fill=hair_a)
    d.pieslice((645, 65, 960, 430), 180, 360, fill=hair_b)
    d.polygon([(665, 210), (682, 88), (755, 45), (850, 62), (942, 150), (916, 315),
               (885, 235), (845, 190), (810, 264), (775, 188), (730, 270), (700, 230)],
              fill=hair_b)
    # Eyes, brows, blush and small smiles.
    for cx, cy, skin in [(430, 265, skin_a), (790, 265, skin_b)]:
        d.arc((cx-54, cy-48, cx-7, cy-10), 190, 345, fill=(66, 56, 58), width=5)
        d.arc((cx+7, cy-48, cx+54, cy-10), 190, 345, fill=(66, 56, 58), width=5)
        d.ellipse((cx-45, cy+10, cx-14, cy+25), fill=(218, 151, 145))
        d.ellipse((cx+14, cy+10, cx+45, cy+25), fill=(218, 151, 145))
        d.arc((cx-18, cy+35, cx+20, cy+68), 5, 170, fill=(126, 74, 77), width=4)
    # Small shared heart motif between the couple.
    hx, hy = 640, 250
    d.ellipse((hx-25, hy-12, hx+3, hy+18), fill=(184, 112, 120))
    d.ellipse((hx-3, hy-12, hx+25, hy+18), fill=(184, 112, 120))
    d.polygon([(hx-24, hy+4), (hx+24, hy+4), (hx, hy+38)], fill=(184, 112, 120))
    return image


async def get_thumb(videoid: str, title: str = "Now Playing", source: str = "YouTube", duration: str = "Music") -> str:
    """Return a fresh Zayn × Alfiya couple artwork for each normal /play request."""
    # Artwork must never wait on a second YouTube metadata request.
    # The track title is already shown in the Telegram caption/player panel.
    title = (title or "Now Playing").strip()
    source = (source or "Music").strip()
    duration_text = (duration or "Music").strip()

    bg = _draw_original_couple_scene().convert("RGBA")
    draw = ImageDraw.Draw(bg)
    try:
        title_font = ImageFont.truetype("SayaMusic/assets/thumb/font2.ttf", 34)
        regular_font = ImageFont.truetype("SayaMusic/assets/thumb/font.ttf", 20)
        brand_font = ImageFont.truetype("SayaMusic/assets/thumb/font2.ttf", 27)
    except OSError:
        title_font = regular_font = brand_font = ImageFont.load_default()

    # Matte ivory title plaque: intentionally no neon, glow, or bright gradients.
    draw.rounded_rectangle((270, 25, 1010, 92), radius=30,
                           fill=(250, 247, 241, 238), outline=(192, 159, 151, 255), width=2)
    draw.text((640, 59), "ZAYN  ×  ALFIYA", fill=(71, 54, 57), font=brand_font, anchor="mm")

    # Track information stays readable without replacing the couple artwork.
    draw.rounded_rectangle((115, 545, 1165, 695), radius=28,
                           fill=(250, 247, 241, 232), outline=(192, 159, 151, 255), width=2)
    draw.text((160, 565), trim_to_width(title, title_font, 950),
              fill=(48, 43, 47), font=title_font)
    draw.text((160, 622), f"{source}  ·  ZYN MUSIC", fill=(105, 86, 87), font=regular_font)

    # Minimal progress motif and duration.
    draw.rounded_rectangle((160, 665, 1080, 674), radius=5, fill=(218, 207, 199))
    draw.rounded_rectangle((160, 665, 420, 674), radius=5, fill=(166, 117, 120))
    draw.text((1080, 645), duration_text, fill=(105, 86, 87), font=regular_font, anchor="ra")

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_couple_{uuid.uuid4().hex[:8]}_v7.png")
    bg.convert("RGB").save(cache_path, quality=94)

    # Keep a small rolling cache: old one-off artwork files are not retained forever.
    try:
        now = time.time()
        prefix = f"{videoid}_couple_"
        for name in os.listdir(CACHE_DIR):
            if name.startswith(prefix) and name.endswith("_v7.png"):
                old_path = os.path.join(CACHE_DIR, name)
                if old_path != cache_path and now - os.path.getmtime(old_path) > 86400:
                    os.remove(old_path)
    except OSError:
        pass

    return cache_path

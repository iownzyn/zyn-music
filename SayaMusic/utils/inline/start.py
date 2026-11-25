# ZYN MUSIC
from pyrogram.types import InlineKeyboardButton

import config
from SayaMusic import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="Add me to your group",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(
                text="Help",
                callback_data="open_help",
            )
        ],
        [
            InlineKeyboardButton(text="Support", url=config.SUPPORT_CHAT),
            InlineKeyboardButton(text="Channel", url=config.SUPPORT_CHANNEL),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="Add me to your group",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(
                text="Help",
                callback_data="open_help",
            )
        ],
        [
            InlineKeyboardButton(text="Support", url=config.SUPPORT_CHAT),
            InlineKeyboardButton(text="Channel", url=config.SUPPORT_CHANNEL),
        ],
    ]
    return buttons

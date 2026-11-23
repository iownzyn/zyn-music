# ZYN MUSIC
import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from SayaMusic import LOGGER, app, userbot
from SayaMusic.core.call import StreamController
from SayaMusic.misc import sudo
from SayaMusic.plugins import ALL_MODULES
from SayaMusic.utils.database import get_banned_users, get_gbanned
from SayaMusic.utils.cookie_handler import fetch_and_store_cookies
from config import BANNED_USERS


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("STRING_SESSION is missing. Add a Pyrogram assistant session in your private environment variables.")
        exit()

    #  Try to fetch cookies at startup
    try:
        await fetch_and_store_cookies()
        LOGGER("SayaMusic").info("ʏᴏᴜᴛᴜʙᴇ ᴄᴏᴏᴋɪᴇs ʟᴏᴀᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ ")
    except Exception as e:
        LOGGER("SayaMusic").warning(f"ᴄᴏᴏᴋɪᴇ ᴇʀʀᴏʀ: {e}")


    await sudo()

    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass

    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("SayaMusic.plugins" + all_module)

    LOGGER("SayaMusic.plugins").info("ZYN MUSIC modules loaded.")

    await userbot.start()
    await StreamController.start()

    try:
        await StreamController.stream_call("http://docs.evostream.com/sample_content/assets/sintel1m720p.mp4")
    except NoActiveGroupCall:
        LOGGER("SayaMusic").error(
            "Please turn on the voice chat of your log group/channel.\n\nZYN MUSIC stopped."
        )
        exit()
    except:
        pass

    await StreamController.decorators()
    LOGGER("SayaMusic").info("ZYN MUSIC bot started successfully.")
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("SayaMusic").info("Stopping ZYN MUSIC bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())

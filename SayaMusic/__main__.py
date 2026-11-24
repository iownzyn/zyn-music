# ZYN MUSIC
import asyncio
import importlib
import os

from aiohttp import web

from pyrogram import idle

import config
from SayaMusic import LOGGER, app, userbot
from SayaMusic.core.call import StreamController
from SayaMusic.misc import sudo
from SayaMusic.plugins import ALL_MODULES
from SayaMusic.utils.database import get_banned_users, get_gbanned
from SayaMusic.utils.cookie_handler import fetch_and_store_cookies
from config import BANNED_USERS

# Readiness is separate from liveness: Render must not mistake a half-started
# process for a fully operational Telegram bot.
_runtime = {"ready": False, "stage": "starting"}


async def health(_request):
    return web.Response(text="ZYN MUSIC process is alive", status=200)


async def readiness(_request):
    if not _runtime["ready"]:
        return web.json_response(
            {"ok": False, "stage": _runtime["stage"]}, status=503
        )
    return web.json_response({"ok": True, "stage": "ready"}, status=200)


async def init():
    if not any((config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5)):
        LOGGER(__name__).error(
            "STRING_SESSION is missing. Add a Pyrogram assistant session in your private environment variables."
        )
        raise SystemExit(1)

    web_app = web.Application()
    web_app.router.add_get("/", health)
    web_app.router.add_get("/health", health)
    web_app.router.add_get("/ready", readiness)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "8080")))
    await site.start()

    try:
        _runtime["stage"] = "loading_database"
        await sudo()

        try:
            users = await get_gbanned()
            for user_id in users:
                BANNED_USERS.add(user_id)
            users = await get_banned_users()
            for user_id in users:
                BANNED_USERS.add(user_id)
        except Exception as exc:
            LOGGER(__name__).warning(
                "Could not preload banned-user lists: %s", type(exc).__name__
            )

        # Bot authorization is the critical startup gate. A timeout here is
        # generally a Telegram MTProto/network/token problem, not a health issue.
        _runtime["stage"] = "telegram_bot_authorization"
        try:
            await app.start()
        except Exception as exc:
            LOGGER(__name__).error(
                "Telegram bot authorization failed (%s). Check BOT_TOKEN with Bot API getMe, "
                "and check Render outbound connectivity to Telegram.",
                type(exc).__name__,
            )
            raise

        _runtime["stage"] = "loading_plugins"
        for all_module in ALL_MODULES:
            importlib.import_module("SayaMusic.plugins" + all_module)
        LOGGER("SayaMusic.plugins").info("ZYN MUSIC modules loaded.")

        # Cookie fetching uses its own requests client; do it only after the
        # bot is authorized and only when a private cookie URL is configured.
        if config.COOKIE_URL:
            try:
                await fetch_and_store_cookies()
                LOGGER("SayaMusic").info("YouTube cookies loaded successfully.")
            except Exception as exc:
                LOGGER("SayaMusic").warning(
                    "Optional YouTube cookie fetch failed (%s). Continuing without cookies.",
                    type(exc).__name__,
                )

        _runtime["stage"] = "starting_assistants"
        await userbot.start()
        await StreamController.start()
        await StreamController.decorators()

        # Do not require an active voice chat in the logger group at boot.
        # Playback is tested naturally when a user issues /play in a group.
        _runtime["ready"] = True
        _runtime["stage"] = "ready"
        LOGGER("SayaMusic").info("ZYN MUSIC bot started successfully.")
        await idle()

    finally:
        _runtime["ready"] = False
        _runtime["stage"] = "stopping"
        try:
            await StreamController.stop()
        except Exception:
            pass
        try:
            await app.stop()
        except Exception:
            pass
        try:
            await userbot.stop()
        except Exception:
            pass
        await runner.cleanup()
        LOGGER("SayaMusic").info("Stopping ZYN MUSIC bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())

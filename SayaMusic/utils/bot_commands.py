# ZYN MUSIC
"""Build Telegram's slash-command suggestions from the commands actually registered by plugins."""

import ast
import logging
import re
from pathlib import Path

from pyrogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
)

LOGGER = logging.getLogger(__name__)

DESCRIPTIONS = {
    "start": "Open ZYN MUSIC and its main menu",
    "help": "Browse all bot features and command categories",
    "play": "Play a song in the group voice chat",
    "search": "Search tracks on RiteshYT",
    "vplay": "Play HD video in the group voice chat",
    "pause": "Pause the current song",
    "resume": "Resume the paused song",
    "skip": "Skip to the next queued song",
    "stop": "Stop playback and clear the queue",
    "end": "End the voice-chat stream",
    "queue": "Show the current music queue",
    "seek": "Jump forward by the given number of seconds",
    "seekback": "Jump backward by the given number of seconds",
    "forward": "Jump forward 10 seconds",
    "forward10": "Jump forward 10 seconds",
    "back": "Jump backward 10 seconds",
    "back10": "Jump backward 10 seconds",
    "rewind10": "Jump backward 10 seconds",
    "speed": "Change playback speed",
    "volume": "Change playback volume",
    "groupmode": "Configure group playback-control permissions",
    "chess": "Start a chess game",
    "dice": "Roll a dice",
}

COMMAND_PATTERN = re.compile(r"^[a-z0-9_]{1,32}$")
PRIORITY = [
    "start", "help", "play", "search", "vplay", "pause", "resume", "skip", "stop",
    "end", "queue", "seek", "seekback", "forward", "back", "forward10",
    "back10", "rewind10", "speed", "volume", "groupmode", "chess", "dice",
]


def _literal_commands(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [item for item in value if isinstance(item, str)]
    return []


def _discover_commands():
    plugin_root = Path(__file__).resolve().parents[1] / "plugins"
    discovered = set()
    for source in plugin_root.glob("*/*.py"):
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            LOGGER.exception("Could not inspect command definitions in %s", source)
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if not isinstance(function, ast.Attribute) or function.attr != "command":
                continue
            if not node.args:
                continue
            for command in _literal_commands(node.args[0]):
                command = command.lower().lstrip("/")
                if COMMAND_PATTERN.fullmatch(command):
                    discovered.add(command)
    return discovered


def build_bot_commands():
    discovered = _discover_commands()
    ordered = [name for name in PRIORITY if name in discovered]
    ordered.extend(sorted(discovered.difference(ordered)))
    # Telegram Bot API allows at most 100 commands per scope.
    ordered = ordered[:100]
    return [
        BotCommand(
            command=name,
            description=DESCRIPTIONS.get(name, f"Run /{name} command"),
        )
        for name in ordered
    ]


async def register_telegram_commands(client):
    commands = build_bot_commands()
    if not commands:
        LOGGER.warning("No Telegram commands discovered; keeping existing command menu.")
        return
    try:
        await client.set_bot_commands(
            commands, scope=BotCommandScopeAllGroupChats()
        )
        await client.set_bot_commands(
            commands, scope=BotCommandScopeAllPrivateChats()
        )
        LOGGER.info("Published %d Telegram slash commands in group and private chats.", len(commands))
    except Exception as exc:
        LOGGER.exception("Could not publish Telegram slash-command menu: %s", type(exc).__name__)

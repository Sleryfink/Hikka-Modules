__version__ = (1, 0, 0)

"""

    .oooooo..o oooo                                  .o88o.  o8o              oooo
    d8P'    `Y8 `888                                  888 `"  `"'              `888
    Y88bo.       888   .ooooo.  oooo d8b oooo    ooo o888oo  oooo  ooo. .oo.    888  oooo
    `"Y8888o.   888  d88' `88b `888""8P  `88.  .8'   888    `888  `888P"Y88b   888 .8P'
        `"Y88b  888  888ooo888  888       `88..8'    888     888   888   888   888888.
    oo     .d8P  888  888    .o  888        `888'     888     888   888   888   888 `88b.
    8""88888P'  o888o `Y8bod8P' d888b        .8'     o888o   o888o o888o o888o o888o o888o
                                        .o..P'
                                        `Y8P'

    Copyleft 2022 t.me/Sleryfink

"""
# meta developer: @Sleryfink
# inspired by @vsecoder_m
import logging
import asyncio
import aiohttp
from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import FloodWaitError, MessageNotModifiedError
from .. import loader, utils  # type: ignore

logger = logging.getLogger(__name__)

async def fetch_track_by_id(track_id, token):
    url = f"https://api.mipoh.ru/songs?track_ids={track_id}&ya_token={token}"
    timeout = aiohttp.ClientTimeout(total=15, connect=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {"success": False, "error": f"HTTP Error: {response.status}", "track": None}

                data = await response.json()

                # Проверяем, есть ли нужные поля в ответе
                if not data or 'track_id' not in data[0]:
                    return {"success": False, "error": "Invalid response format", "track": None}

                return {
                    "track_id": data[0]["track_id"],
                    "title": data[0]["title"],
                    "artist": data[0]["artist"],
                    "img": data[0]["img"],
                    "duration": data[0]["duration"],
                    "download_link": data[0]["download_link"],
                    "success": True,
                }

    except Exception as e:
        return {"success": False, "error": str(e), "track": None}

@loader.tds
class YmFLink(loader.Module):
    """
    Get music from Yandex Music via link
    On api.mipoh.ru API.
    """

    strings = {
        "name": "YmFLink",
        "no_token": "<b><emoji document_id=5843952899184398024>🚫</emoji> Specify a token in config!</b>",
        "playing": "<b><emoji document_id=5188705588925702510>🎶</emoji> Track: </b><code>{}</code><b> - </b><code>{}</code>",
        "no_args": "<b><emoji document_id=5843952899184398024>🚫</emoji> Provide arguments!</b>",
        "_cls_doc": "Module for Yandex Music, based on api.mipoh.ru",
        "no_results": "<b><emoji document_id=5285037058220372959>☹️</emoji> No results found :(</b>",
        "_cfg_yandexmusictoken": "Yandex.Music account token",
        "guide": (
            '<a href="https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781">'
            "Instructions for obtaining a Yandex.Music token</a>"
        ),
    }
    strings_ru = {
        "no_token": "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажите токен в конфигурации!</b>",
        "playing": "<b><emoji document_id=5188705588925702510>🎶</emoji> Трек: </b><code>{}</code><b> - </b><code>{}</code>",
        "no_args": "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажите аргументы!</b>",
        "_cls_doc": "Модуль для Yandex Music, основанный на api.mipoh.ru",
        "no_results": "<b><emoji document_id=5285037058220372959>☹️</emoji> Результаты не найдены :(</b>",
        "_cfg_yandexmusictoken": "Токен аккаунта Yandex.Music",
        "guide": (
            '<a href="https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781">'
            "Инструкция по получению токена Yandex.Music</a>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "YandexMusicToken",
                None,
                lambda: self.strings["_cfg_yandexmusictoken"],
                validator=loader.validators.Hidden(),
            ),
        )

    async def client_ready(self, client: TelegramClient, db):
        self.client = client
        self.db = db

    @loader.command()
    async def yget(self, message: Message):
        """Get track info from provided Yandex Music link"""

        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        # Extracting track ID from the provided link
        args = utils.get_args(message)

        if not args:
            await utils.answer(message, self.strings["no_args"])
            return

        # Assuming the first argument is the link
        link = args[0]

        # Extract track ID from the link (this may need adjustment based on actual link format)
        try:
            track_id = link.split('/')[-1].split('?')[0]  # Example: Extracting from /track/110661937
            if not track_id.isdigit():
                raise ValueError("Track ID is not valid.")

        except Exception as e:
            await utils.answer(message, f"<b>Error extracting track ID:</b> {str(e)}")
            return

        # Fetching track details by ID
        res = await fetch_track_by_id(track_id, self.config["YandexMusicToken"])

        if not res["success"]:
            await utils.answer(message, self.strings["no_results"])
            return

        track = res  # Track is now an object returned by fetch_track_by_id
        lnk = track["track_id"]
        # Forming response text with track details
        caption = self.strings["playing"].format(
            utils.escape_html(track["title"]),
            utils.escape_html(track["artist"]),
        )

        # Sending response with information about the track and download link
        await self.inline.form(
            message=message,
            text=caption,
            reply_markup={
                "text": "song.link",
                "url": f"https://song.link/ya/{lnk}",
            },
            silent=True,
            audio={
                "url": track["download_link"],
                "title": utils.escape_html(track["title"]),
                "performer": utils.escape_html(track["artist"]),
            },
        )
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
import logging
import aiohttp
import random
import json
import string
from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import FloodWaitError, MessageNotModifiedError
from telethon.tl.functions.account import UpdateProfileRequest
from .. import loader, utils  # type: ignore

logger = logging.getLogger(__name__)
async def get_current_track(token):
    url = f"https://api.mipoh.ru/get_current_track_beta?ya_token={token}"
    timeout = aiohttp.ClientTimeout(total=15, connect=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {"success": False, "error": f"HTTP Error: {response.status}", "track": None}

                data = await response.json()

                # Проверяем, есть ли нужные поля в ответе
                if not data.get("track"):
                    return {"success": False, "error": "Invalid response format", "track": None}

                return {
                    "paused": data.get("paused"),
                    "duration_ms": data.get("duration_ms"),
                    "progress_ms": data.get("progress_ms"),
                    "entity_id": data.get("entity_id"),
                    "entity_type": data.get("entity_type"),
                    "track": data.get("track"),
                    "success": True,
                }

    except Exception as e:
        return {"success": False, "error": str(e), "track": None}

@loader.tds
class YmNowSimple(loader.Module):
    """
    Module for yandex music.
    On api.mipoh.ru API.
    """

    strings = {
        "name": "YmNowS",
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
        "no_token": "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи токен в конфиге!</b>",
        "no_args": "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи аргументы!</b>",
        "playing": "<b><emoji document_id=5188705588925702510>🎶</emoji> Трек: </b><code>{}</code><b> - </b><code>{}</code>",
        "no_results": "<b><emoji document_id=5285037058220372959>☹️</emoji> Ничего не найдено :(</b>",
        "_cls_doc": "Модуль для Яндекс Музыки, на базе api.mipoh.ru",
        "_cfg_yandexmusictoken": "Токен аккаунта Яндекс.Музыка",
        "guide": (
            '<a href="https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781">'
            "Инструкция по получению токена Яндекс.Музыка</a>"
        ),
        "configuring": "🙂 <b>Виджет готов и скоро будет обновлен</b>",
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

    async def on_dlmod(self):
        if not self.get("guide_send", False):
            await self.inline.bot.send_message(
                self._tg_id,
                self.strings["guide"],
            )
            self.set("guide_send", True)

    async def client_ready(self, client: TelegramClient, db):
        self.client = client
        self.db = db

    @loader.command()
    async def ynowcmd(self, message: Message):
        """Get now playing track"""

        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        # Получаем данные о текущем треке
        res = await get_current_track(self.config["YandexMusicToken"])

        if not res["success"]:
            await utils.answer(message, self.strings["no_results"])
            return

        track = res["track"]  # track уже является объектом, не массивом, так что можно использовать его напрямую

        # Получаем ссылку для скачивания
        link = track["download_link"]

        # Извлекаем данные о треке
        title = track["title"]
        artist = track["artist"]  # В ответе только один исполнитель

        # Формируем строку с длительностью в формате MM:SS
        caption = self.strings["playing"].format(
            utils.escape_html(title),
            utils.escape_html(artist),  # Только один исполнитель
        )

        # Создаем ссылку для song.link (вы предполагаете, что `track["id"]` существует)
        track_id = track["track_id"]  # Используем track_id для создания ссылки

        # Отправляем ответ с информацией о треке и встроенным проигрывателем
        await self.inline.form(
            message=message,
            text=caption,
            reply_markup={
                "text": "song.link",
                "url": f"https://song.link/ya/{track_id}",  # Используем track_id в ссылке
            },
            silent=True,
            audio={
                "url": link,
                "title": utils.escape_html(title),
                "performer": utils.escape_html(artist),
            },
        )
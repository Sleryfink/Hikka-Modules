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

    t.me/Sleryfink

"""
# meta developer: @Sleryfink
import os
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime
from telethon.tl.types import Message
from .. import loader, utils

@loader.tds
class PinterestVidD(loader.Module):
    """Модуль для загрузки видео с Pinterest"""
    strings = {
        "name": "PinterestVidD",
        "invalid_url": "<b>Введена некорректная ссылка. Пожалуйста, укажите ссылку на пин.</b>",
        "fetching_content": "<b>Получаю содержимое с указанного URL...</b>",
        "downloading": "<b>Скачиваю видео...</b>",
        "sending": "<b>Отправляю видео...</b>",
        "error": "<b>Ошибка:</b> {error}",
    }

    def download_file(self, url, filename):
        response = requests.get(url, stream=True)
        file_size = int(response.headers.get('Content-Length', 0))
        progress = tqdm(
            response.iter_content(1024),
            f"Downloading {filename}",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        )

        with open(filename, "wb") as f:
            for data in progress.iterable:
                f.write(data)
                progress.update(len(data))

    def extract_original_url(self, page_url):
        response = requests.get(page_url)
        if response.status_code != 200:
            raise Exception("URL недействителен или недоступен.")

        soup = BeautifulSoup(response.content, "html.parser")
        href_link = soup.find("link", rel="alternate")["href"]
        match = re.search(r"url=(.*?)&", href_link)
        if not match:
            raise Exception("Не удалось извлечь оригинальную ссылку.")
        return match.group(1)

    def extract_video_url(self, page_url):
        response = requests.get(page_url)
        if response.status_code != 200:
            raise Exception("URL недействителен или недоступен.")

        soup = BeautifulSoup(response.content, "html.parser")
        video_tag = soup.find("video", class_="hwa kVc MIw L4E")
        if not video_tag or "src" not in video_tag.attrs:
            raise Exception("Видео не найдено на странице.")

        extract_url = video_tag["src"]
        return extract_url.replace("hls", "720p").replace("m3u8", "mp4")

    @loader.command()
    async def pinvid(self, message: Message):
        """Скачать видео с Pinterest: .pinvid <ссылка>"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings["invalid_url"])
            return

        page_url = args[0]

        try:
            if "pinterest.com/pin/" not in page_url and "https://pin.it/" not in page_url:
                await utils.answer(message, self.strings["invalid_url"])
                return

            if "https://pin.it/" in page_url:
                await utils.answer(message, self.strings["fetching_content"])
                page_url = self.extract_original_url(page_url)

            video_url = self.extract_video_url(page_url)

            filename = datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + ".mp4"
            await utils.answer(message, self.strings["downloading"])
            self.download_file(video_url, filename)

            await utils.answer(message, self.strings["sending"])
            await message.client.send_file(
                message.to_id,
                file=filename,
                reply_to=message.reply_to_msg_id,
            )
        except Exception as e:
            await utils.answer(message, self.strings["error"].format(error=str(e)))
        finally:
            if os.path.exists(filename):
                os.remove(filename)
                await message.delete()
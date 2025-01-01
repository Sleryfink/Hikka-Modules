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

    2024 t.me/Sleryfink

"""
# meta developer: @Sleryfink
from .. import loader, utils
import os

@loader.tds
class FileSenderMod(loader.Module):
    """Модуль для отправки файлов с сервера"""
    strings = {"name": "FileSender"}

    async def filecmd(self, message):
        """Отправляет файл с сервера. Использование: .file <path/to/file>"""
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("❌ Укажите путь к файлу.")
            return

        file_path = args.strip()

        if os.path.exists(file_path):
            await message.client.send_file(message.chat_id, file_path)
            await message.delete()
        else:
            await message.edit(f"❌ Файл по пути `{file_path}` не найден.")

from typing import Optional, NamedTuple
import aiohttp
import json

from loguru import logger

from config import TG_BOT_TOKEN


class TelegramButton(NamedTuple):
    text: str
    url: str


class TelegramTools:
    async def send_message(
        chat_id: int,
        text: str,
        photo_url: Optional[str] = None,
        button: Optional[TelegramButton] = None
    ) -> bool:
        method = "sendPhoto" if photo_url else "sendMessage"
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/{method}"

        # Основные данные
        data = {
            "chat_id": chat_id,
            "parse_mode": "HTML",
            "caption" if photo_url else "text": text,
        }

        # Добавим URL фото, если есть
        if photo_url:
            data["photo"] = photo_url

        # Добавим кнопку, если передана
        if button:
            reply_markup = {
                "inline_keyboard": [[
                    {"text": button.text, "url": button.url}
                ]]
            }
            data["reply_markup"] = json.dumps(reply_markup)

        # Отправка запроса
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    return True
                else:
                    logger.debug(await response.json())
                    return False
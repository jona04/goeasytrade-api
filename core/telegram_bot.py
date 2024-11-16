import telegram

from telegram import Bot
import asyncio

from constants.defs import (TELEGRAM_TOKEN)


#Define bot
bot = Bot(token=TELEGRAM_TOKEN)

async def send_message(text, chat_id):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)

async def send_photo(photo_path, chat_id):
    async with bot:
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo)

async def run_bot(messages, chat_id):
    for message in messages:
        if isinstance(message, str):  # Se for texto, envia como mensagem
            await send_message(message, chat_id)
        elif isinstance(message, tuple) and message[0] == "photo":  # Se for imagem, envia como foto
            photo_path = message[1]
            await send_photo(photo_path, chat_id)

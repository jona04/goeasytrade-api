import telegram

from telegram import Bot
import asyncio

from constants.defs import (TELEGRAM_TOKEN)


#Define bot
bot = Bot(token=TELEGRAM_TOKEN)

async def send_message(text, chat_id):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)

async def run_bot(messages, chat_id):
    text = '\n'.join(messages)
    await send_message(text, chat_id)

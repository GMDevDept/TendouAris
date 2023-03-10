# https://docs.telethon.dev/en/latest/
# https://platform.openai.com/docs/guides/chat/introduction

import os
import openai
import logging
from collections import deque
from telethon import TelegramClient, events
from util import process_message
from prompts import no_auth

# Unmark if test on Windows
# from dotenv import load_dotenv
# load_dotenv()

logging.basicConfig(
    format="[ %(levelname)s / %(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
whitelist = [int(i) for i in os.getenv("WHITELIST").split(",")]
openai.api_key = os.getenv("OPENAI_API_KEY")

# Telegram bot client
client = TelegramClient("CosGPT", api_id, api_hash)

# Chat history by chat id
history = {int: deque}


# Gate keeper
@client.on(
    events.NewMessage(
        chats=whitelist,
        blacklist_chats=True,
        pattern=r"(/start)|(/aris)",
        func=lambda e: e.is_group,
    )
)
async def permission_handler(event):
    await event.reply(no_auth)


# Private chats
@client.on(events.NewMessage(pattern=r"(/aris)|([^/])", func=lambda e: e.is_private))
async def private_message_handler(event):
    gtp_output = await process_message(event, history)
    await event.reply(gtp_output)


# Group chats
@client.on(
    events.NewMessage(
        chats=whitelist, pattern=r"(/aris)|(爱丽丝)", func=lambda e: e.is_group
    )
)
async def group_message_handler(event):
    gtp_output = await process_message(event, history)
    await event.reply(gtp_output)


def main():
    client.start(bot_token=bot_token)
    client.run_until_disconnected()


if __name__ == "__main__":
    main()

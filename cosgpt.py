# https://docs.telethon.dev/en/stable/
# https://platform.openai.com/docs/guides/chat/introduction

import os
import openai
import logging
from collections import deque
from telethon import TelegramClient, events
from util import process_message
from prompts import no_auth, history_cleared, last_message_cleared

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
auto_clear_count = int(os.getenv("AUTO_CLEAR_COUNT", 0))

# Telegram bot client
client = TelegramClient("CosGPT", api_id, api_hash)

# Chat history by chat id
history = {int: deque}
auto_clear = {int: int}


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


# Get chat id
@client.on(events.NewMessage(pattern=r"/chatid"))
async def chatid_handler(event):
    await event.reply(str(event.chat_id))


# Reset chat history
@client.on(events.NewMessage(pattern=r"/reset"))
async def history_handler1(event):
    history.pop(event.chat_id, history)
    await event.reply(history_cleared)


# Pop chat history
@client.on(events.NewMessage(pattern=r"/pop"))
async def history_handler2(event):
    if event.chat_id in history and len(history[event.chat_id]) >= 2:
        history[event.chat_id].pop()
        history[event.chat_id].pop()
    await event.reply(last_message_cleared)


# Private chats
@client.on(
    events.NewMessage(
        pattern=r"(/aris)|([^/])",
        func=lambda e: e.is_private,
        forwards=False,
    )
)
async def private_message_handler(event):
    gtp_output = await process_message(False, event, history, auto_clear=auto_clear)
    await event.reply(gtp_output)


# Group chats
@client.on(
    events.NewMessage(
        chats=whitelist,
        pattern=r"(/aris)|(爱丽丝)",
        func=lambda e: e.is_group,
        forwards=False,
    )
)
async def group_message_handler(event):
    gtp_output = await process_message(False, event, history, auto_clear=auto_clear)
    await event.reply(gtp_output)


# Group chats direct reply
@client.on(
    events.NewMessage(
        chats=whitelist,
        pattern=r"^(?!/aris|爱丽丝)",  # Avoid duplicate replies
        func=lambda e: e.is_group and e.is_reply,
        forwards=False,
    )
)
async def group_reply_handler(event):
    replied_message = await event.get_reply_message()
    sender = await replied_message.get_sender()
    try:
        if sender.is_self:
            gtp_output = await process_message(
                False, event, history, add_reply=replied_message, auto_clear=auto_clear
            )
            await event.reply(gtp_output)
    # Sender could be Channel object or NoneType object
    except AttributeError as e:
        logging.warning(f"AttributeError: {e}")


# Auto clear chat history in group chats
if auto_clear_count > 0:

    @client.on(
        events.NewMessage(chats=whitelist, incoming=True, func=lambda e: e.is_group)
    )
    async def group_message_counter(event):
        if event.chat_id not in auto_clear:
            auto_clear[event.chat_id] = 0

        auto_clear[event.chat_id] += 1

        if auto_clear[event.chat_id] == auto_clear_count:
            history.pop(event.chat_id, history)
            logging.info(
                f"Chat history for group {event.chat_id} has been cleared due to inactivity"
            )


def main():
    client.start(bot_token=bot_token)
    client.run_until_disconnected()


if __name__ == "__main__":
    main()

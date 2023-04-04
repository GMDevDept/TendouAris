# https://docs.telethon.dev/en/stable/
# https://platform.openai.com/docs/guides/chat/introduction

import os
import re
import redis
import openai
import logging
import prompts
from collections import deque
from telethon import TelegramClient, events
from util import remove_command, history_clear_handler, process_message

logging.basicConfig(
    format="[ %(levelname)s / %(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
manager = [int(i) for i in os.getenv("MANAGER").split(",")]
whitelist = [int(i) for i in os.getenv("WHITELIST").split(",")]

# Telegram bot client
client = TelegramClient("Aris", api_id, api_hash)

# Redis database
db = redis.Redis(host="arisdata", port=6379, db=0, decode_responses=True)

# Get users with custom API key provided
userlist = [int(i) for i in db.keys()]

# Chat history by chat id
history = {int: deque}
auto_clear = {int: int}


# Get version
@client.on(events.NewMessage(pattern=r"/version"))
async def version_handler(event):
    await event.reply("TendouArisBot v1.3")


# Get chat id
@client.on(events.NewMessage(pattern=r"/chatid"))
async def chatid_handler(event):
    await event.reply(str(event.chat_id))


# Reset chat history
@client.on(events.NewMessage(pattern=r"/reset"))
async def history_handler1(event):
    history.pop(event.chat_id, history)
    await event.reply(prompts.history_cleared)


# Pop chat history
@client.on(events.NewMessage(pattern=r"/pop"))
async def history_handler2(event):
    if event.chat_id in history and len(history[event.chat_id]) >= 2:
        history[event.chat_id].pop()
        history[event.chat_id].pop()
    await event.reply(prompts.last_message_cleared)


# Provide own API key
@client.on(events.NewMessage(pattern=r"/apikey"))
async def apikey_handler(event):
    apikey_input = remove_command(event.raw_text)
    if apikey_input.startswith("sk-"):
        try:
            await openai.ChatCompletion.acreate(
                api_key=apikey_input,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Test message, please reply '1'"}
                ],
            )

            db.set(event.chat_id, apikey_input)
            if event.chat_id not in userlist:
                userlist.append(event.chat_id)
            await event.reply(prompts.api_key_set)
        except openai.error.OpenAIError as e:
            await event.reply(f"{prompts.api_key_invalid}\n\n({e})")
    else:
        await event.reply(prompts.api_key_invalid)


# Set API key for other user (manager only)
@client.on(events.NewMessage(chats=manager, pattern=r"/fapikey"))
async def fapikey_handler(event):
    chatid_input, apikey_input = remove_command(event.raw_text).split()
    try:
        db.set(chatid_input, apikey_input)
        if chatid_input not in userlist:
            userlist.append(chatid_input)
        await event.reply(prompts.api_key_set)
    except Exception as e:
        await event.reply(e)


# Private chat
@client.on(
    events.NewMessage(
        pattern=r"(/start)|(/aris)|([^/])",
        func=lambda event: event.is_private,
        forwards=False,
    )
)
async def private_message_handler(event):
    if event.chat_id not in whitelist + userlist:
        output_message = prompts.no_auth
    else:
        output_message = await process_message(
            event,
            db=db,
            retry=False,
            history=history,
            userlist=userlist,
            whitelist=whitelist,
        )

    await event.reply(output_message)


# Group chat
@client.on(
    events.NewMessage(
        func=lambda event: event.is_group,
        forwards=False,
    )
)
async def group_message_handler(event):
    if event.chat_id not in whitelist + userlist:
        if re.match(r"^(/aris)|(爱丽丝)", event.raw_text):
            output_message = prompts.no_auth
        else:
            return
    else:
        if event.is_reply:
            reply_message = await event.get_reply_message()
            # Direct reply
            if reply_message.sender_id == (await client.get_me()).id:
                if re.match(r"^(?!/)", event.raw_text):
                    add_reply = {
                        "role": "assistant",
                        "content": reply_message.raw_text,
                    }
                # Messages start with command should be handled elsewhere (direct reply with /aris is alse ignored)
                else:
                    return
            # Reply to other user's message, handle as quote
            else:
                if re.match(r"^(/aris)|(爱丽丝)", event.raw_text):
                    add_reply = {
                        "role": "user",
                        "content": remove_command(reply_message.raw_text),
                    }
                else:
                    history_clear_handler(event, auto_clear, history)
                    return
        # Not a reply
        else:
            if re.match(r"^(/aris)|(爱丽丝)", event.raw_text):
                add_reply = False
            else:
                history_clear_handler(event, auto_clear, history)
                return

        output_message = await process_message(
            event,
            db=db,
            retry=False,
            history=history,
            userlist=userlist,
            whitelist=whitelist,
            add_reply=add_reply,
            auto_clear=auto_clear,
        )

    await event.reply(output_message)


def main():
    client.start(bot_token=bot_token)
    client.run_until_disconnected()


if __name__ == "__main__":
    main()

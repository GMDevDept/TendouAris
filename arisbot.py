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
flood_control_count = int(os.getenv("FLOOD_CONTROL_COUNT"))
flood_control_delay = int(os.getenv("FLOOD_CONTROL_DELAY"))
manager = [int(i) for i in os.getenv("MANAGER").split(",")]
whitelist = [int(i) for i in os.getenv("WHITELIST").split(",")]

# Telegram bot client
client = TelegramClient("Aris", api_id, api_hash)

# Redis database
db_apikey = redis.Redis(host="arisdata", port=6379, db=0, decode_responses=True)
db_floodctrl = redis.Redis(host="arisdata", port=6379, db=1, decode_responses=True)

# Get users with custom API key provided
userlist = [int(i) for i in db_apikey.keys()]

# Flood control by user in groups
flood_ctrl = {
    int(i): {} for i in db_floodctrl.keys()
}  # {chatid: {user_id: token counter}}

# Chat history by chat id
history = {int: deque}
auto_clear = {int: int}


# Get version
@client.on(events.NewMessage(pattern=r"/version"))
async def version_handler(event):
    await event.reply("TendouArisBot v1.3.1")


# Welcome/help message
@client.on(events.NewMessage(pattern=r"(/start)|(/help)"))
async def help_handler(event):
    sender = await event.get_sender()
    name = f"{sender.first_name and sender.first_name or ''} {sender.last_name and sender.last_name or ''}".strip()
    await event.reply(prompts.manual.format(name), parse_mode="html")


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
    if event.chat_id in history and len(history[event.chat_id]) > 2:
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

            db_apikey.set(event.chat_id, apikey_input)
            if event.chat_id not in userlist:
                userlist.append(event.chat_id)
            await event.reply(prompts.api_key_set)
        except openai.error.OpenAIError as e:
            await event.reply(f"{prompts.api_key_invalid}\n\n({e})", parse_mode="html")
    else:
        await event.reply(prompts.api_key_invalid, parse_mode="html")


# Set API key for other user (manager only)
@client.on(events.NewMessage(chats=manager, pattern=r"/fapikey"))
async def fapikey_handler(event):
    inputs = remove_command(event.raw_text).split()
    try:
        chatid_input, apikey_input = inputs
        db_apikey.set(chatid_input, apikey_input)
        if chatid_input not in userlist:
            userlist.append(chatid_input)
        await event.reply(prompts.api_key_set)
    except ValueError as e:
        if len(inputs) == 1:
            chatid_input = inputs[0]
            db_apikey.delete(chatid_input)
            if chatid_input in userlist:
                userlist.remove(chatid_input)
            await event.reply(prompts.api_key_set)
        else:
            await event.reply(e)
    except Exception as e:
        await event.reply(e)


# Activate/deactivate flood control in a group chat (manager only)
@client.on(events.NewMessage(chats=manager, pattern=r"/fctrl"))
async def flood_control_handler(event):
    try:
        chatid_input = int(remove_command(event.raw_text))
        if chatid_input not in flood_ctrl:
            flood_ctrl[chatid_input] = {}
            db_floodctrl.set(chatid_input, 1)
            await event.reply(f"Flood control activated for chat {chatid_input}")
        else:
            flood_ctrl.pop(chatid_input)
            db_floodctrl.delete(chatid_input)
            await event.reply(f"Flood control deactivated for chat {chatid_input}")
    except Exception as e:
        await event.reply(e)


# Private chat
@client.on(
    events.NewMessage(
        pattern=r"(/aris)|([^/])",
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
            retry=False,
            history=history,
            userlist=userlist,
            whitelist=whitelist,
            db_apikey=db_apikey,
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
        # Filter cases where API request is not needed
        # When message is a reply, generate add_reply before processing
        if event.is_reply:
            reply_message = await event.get_reply_message()
            # Direct reply
            if reply_message.sender_id == (await client.get_me()).id:
                # Match all messages which don't start with command
                if re.match(r"^(?!/)", event.raw_text):
                    # No need to add reply if the last message is the same
                    if (
                        event.chat_id in history
                        and len(history[event.chat_id]) > 0
                        and history[event.chat_id][-1].get("content")
                        == reply_message.raw_text
                    ):
                        add_reply = False
                    else:
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

        # Check if flood control is active before sending API request
        if (
            event.chat_id in flood_ctrl
            and event.sender_id is not None  # Anonymous group admin
            and event.sender_id in flood_ctrl[event.chat_id]
            and flood_ctrl[event.chat_id][event.sender_id] > flood_control_count
            and db_apikey.get(event.sender_id) is None
        ):
            output_message = prompts.flood_control_activated.format(
                flood_control_delay,
                flood_ctrl[event.chat_id][event.sender_id],
                flood_control_count,
            )
        else:
            # Bypass if user has provided API key
            if (
                event.chat_id in flood_ctrl
                and event.sender_id is not None  # Anonymous group admin
                and event.sender_id in flood_ctrl[event.chat_id]
                and flood_ctrl[event.chat_id][event.sender_id] > flood_control_count
                and db_apikey.get(event.sender_id) is not None
            ):
                backup_key = db_apikey.get(event.sender_id)
            else:
                backup_key = None

            output_message = await process_message(
                event,
                retry=False,
                history=history,
                userlist=userlist,
                whitelist=whitelist,
                add_reply=add_reply,
                db_apikey=db_apikey,
                auto_clear=auto_clear,
                backup_key=backup_key,
                flood_ctrl=event.chat_id in flood_ctrl and flood_ctrl,
            )

    await event.reply(output_message)


def main():
    client.start(bot_token=bot_token)
    client.run_until_disconnected()


if __name__ == "__main__":
    main()

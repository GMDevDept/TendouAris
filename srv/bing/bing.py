# https://github.com/acheong08/EdgeGPT

import os
import re
import asyncio
import logging
from EdgeGPT import Chatbot, ConversationStyle

bing_chatbot_close_delay = int(os.getenv("BING_CHATBOT_CLOSE_DELAY", 600))


async def process_message_bing(event, **kwargs):
    style = kwargs.get("style", "creative")
    bing_chatbot = kwargs.get("bing_chatbot")

    match style:
        case "creative":
            conversation_style = ConversationStyle.creative
        case "balanced":
            conversation_style = ConversationStyle.balanced
        case "precise":
            conversation_style = ConversationStyle.precise
        case _:
            return f"Invalid conversation style: {style}"

    if event.chat_id not in bing_chatbot:
        bing_chatbot[event.chat_id] = [
            await Chatbot.create(cookie_path="./srv/bing/cookies.json"),
            0,
        ]

    bot = bing_chatbot[event.chat_id][0]

    response = await bot.ask(
        prompt=re.sub(r"^/\S*", "", event.raw_text).strip().replace("爱丽丝", "Bing"),
        conversation_style=conversation_style,
    )

    output_text = response["item"]["messages"][1]["text"]
    log = response["item"]["result"]

    logging.info(f"Request result from bing.com: {log}")

    bing_chatbot[event.chat_id][1] += 1

    async def scheduled_auto_close():
        await asyncio.sleep(bing_chatbot_close_delay)
        if event.chat_id in bing_chatbot:  # Could be manually closed
            bing_chatbot[event.chat_id][1] -= 1
            if bing_chatbot[event.chat_id][1] == 0:
                await bot.close()
                bing_chatbot.pop(event.chat_id, bing_chatbot)
                logging.info(
                    f"Bing chatbot for chat {event.chat_id} has been closed due to inactivity"
                )

    asyncio.create_task(scheduled_auto_close())

    return output_text

# https://github.com/acheong08/EdgeGPT

import os
import re
import asyncio
import logging
import prompts
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
            False,
        ]
    # Block new requests if the bot is being used
    elif bing_chatbot[event.chat_id][2]:
        return f"{prompts.api_error}\n\n({prompts.chat_concurrent_blocked})"

    bing_chatbot[event.chat_id][2] = True

    try:
        bot = bing_chatbot[event.chat_id][0]
        input_text = re.sub(r"^/\S*", "", event.raw_text).strip()
        if input_text.startswith("爱丽丝"):
            input_text = input_text.replace("爱丽丝", "Bing", 1)
        response = await bot.ask(
            prompt=input_text,
            conversation_style=conversation_style,
        )
    except Exception as e:
        bing_chatbot[event.chat_id][2] = False
        logging.error(f"Error happened when calling bot.ask: {e}")
        return f"{prompts.api_error}\n\n({e})"

    bing_chatbot[event.chat_id][2] = False

    output_text = response["item"]["messages"][1]["text"]
    sourceAttributions = response["item"]["messages"][1]["sourceAttributions"]
    if len(sourceAttributions) > 0:
        output_text = re.sub(r"\[\^(\d+)\^\]", r"[\1]", output_text)
        reference_links = "\n".join(
            [
                f"[{i+1}] [{sourceAttributions[i]['providerDisplayName']}]({sourceAttributions[i]['seeMoreUrl']})"
                for i in range(len(sourceAttributions))
            ]
        )
        reference_text = f"\n\nReferences:\n{reference_links}"
        output_text = output_text + reference_text

    log = response["item"]["result"]
    logging.info(f"Request result from bing.com: {log}")

    if bing_chatbot_close_delay > 0:
        bing_chatbot[event.chat_id][1] += 1

        async def scheduled_auto_close():
            await asyncio.sleep(bing_chatbot_close_delay)
            if event.chat_id in bing_chatbot:  # Could be manually closed
                bing_chatbot[event.chat_id][1] = max(
                    0, bing_chatbot[event.chat_id][1] - 1
                )
                if bing_chatbot[event.chat_id][1] == 0:
                    await bot.close()
                    bing_chatbot.pop(event.chat_id, bing_chatbot)
                    logging.info(
                        f"Bing chatbot for chat {event.chat_id} has been closed due to inactivity"
                    )

        asyncio.create_task(scheduled_auto_close())

    return output_text

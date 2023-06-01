# https://github.com/acheong08/Bard

import os
import re
import json
import asyncio
import logging
import prompts
from Bard import Chatbot

google_bard_cookie = os.getenv("GOOGLE_BARD_COOKIE", None)
bard_chatbot_close_delay = int(os.getenv("BARD_CHATBOT_CLOSE_DELAY", 600))


async def process_message_bard(event, **kwargs):
    if not google_bard_cookie:
        return {
            "output_text": "Please set the GOOGLE_BARD_COOKIE environment variable to use this feature."
        }

    preset = kwargs.get("preset", "default")
    bard_chatbot = kwargs.get("bard_chatbot")

    if event.chat_id not in bard_chatbot:
        bard_chatbot[event.chat_id] = [
            Chatbot(google_bard_cookie),
            0,
            False,
        ]
    # Block new requests if the bot is being used
    elif bard_chatbot[event.chat_id][2]:
        return {
            "output_text": f"{prompts.api_error}\n\n({prompts.chat_concurrent_blocked})"
        }

    bard_chatbot[event.chat_id][2] = True

    try:
        bot = bard_chatbot[event.chat_id][0]
        input_text = re.sub(r"^/\S*", "", event.raw_text).strip()
        if input_text.startswith("爱丽丝"):
            input_text = input_text.replace("爱丽丝", "Bard", 1)
        if preset == "cn":
            input_text = prompts.bard_cn_prompt.format(input_text)
        response = bot.ask(input_text)
    except Exception as e:
        bard_chatbot[event.chat_id][2] = False
        logging.error(f"Error happened when calling bot.ask: {e}")
        return {"output_text": f"{prompts.api_error}\n\n({e})"}

    bard_chatbot[event.chat_id][2] = False

    output_text = response["content"]
    if preset == "cn":
        try:
            # Match json object in the output text
            output_json = re.match(r".*?({.*}).*", output_text, re.DOTALL).group(1)
            output_dict = json.loads(output_json)
            output_text = (
                output_dict["en_response"]
                + "\n\n"
                + output_dict["en_response_translated_to_cn"]
            )
        except (AttributeError, json.JSONDecodeError):
            # Handle cases where the regular expression pattern does not match anything
            # or the resulting substring is not a valid JSON object
            pass  # Return raw text

    output_file = None
    images = response["images"]  # set, {link1, link2}
    if len(images) > 0:
        output_file = list(images)
        output_text = re.sub(r"\n\[.*\]", "", output_text)

    log = response["conversation_id"]
    logging.info(f"Requesting bard.google.com succeeded: conversation_id={log}")

    if bard_chatbot_close_delay > 0:
        bard_chatbot[event.chat_id][1] += 1

        async def scheduled_auto_close():
            await asyncio.sleep(bard_chatbot_close_delay)
            if event.chat_id in bard_chatbot:  # Could be manually closed
                bard_chatbot[event.chat_id][1] = max(
                    0, bard_chatbot[event.chat_id][1] - 1
                )
                if bard_chatbot[event.chat_id][1] == 0:
                    chatbot = bard_chatbot[event.chat_id][0]
                    chatbot.conversation_id = ""
                    chatbot.response_id = ""
                    chatbot.choice_id = ""
                    bard_chatbot.pop(event.chat_id, bard_chatbot)
                    logging.info(
                        f"Bard chatbot for chat {event.chat_id} has been closed due to inactivity"
                    )

        asyncio.create_task(scheduled_auto_close())

    return {"output_text": output_text, "output_file": output_file}

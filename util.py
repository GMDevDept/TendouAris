import os
import re
import random
import logging
import prompts
from srv.gpt.gpt import process_message_gpt
from srv.bing.bing import process_message_bing

auto_clear_count = int(os.getenv("AUTO_CLEAR_COUNT", 0))


def remove_command(text):
    return re.sub(r"^/\S*", "", text).strip()


def history_clear_handler(event, auto_clear, history):
    if auto_clear_count > 0:
        if event.chat_id not in auto_clear:
            auto_clear[event.chat_id] = 0

        auto_clear[event.chat_id] += 1

        if auto_clear[event.chat_id] == auto_clear_count:
            history.pop(event.chat_id, history)
            logging.info(
                f"Chat history for group {event.chat_id} has been cleared due to inactivity"
            )


async def process_message(event, **kwargs):
    model = kwargs.get("model").get(event.chat_id)

    placeholder_text = random.choice(prompts.placeholder_before_output)
    placeholder_reply = await event.reply(placeholder_text)

    if not model:
        output_text = await process_message_gpt(event, **kwargs)
    elif model.get("name") == "model-bing":
        await placeholder_reply.edit(placeholder_text + prompts.placeholer_bing)
        output_text = await process_message_bing(
            event, style=model.get("bingstyle"), **kwargs
        )
    else:
        output_text = f"Invalid model: {model}"

    return output_text, placeholder_reply

import os
import re
import openai
from collections import deque
from prompts import system_prompt, initial_prompts, text_filters

max_history = int(os.getenv("MAX_HISTORY", 10))
max_tokens = int(os.getenv("MAX_TOKENS", 1024))


def remove_command(text):
    return re.sub(r"^/\S*", "", text).strip()


async def process_message(event, history, **kwargs):
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
    ]

    if event.chat_id not in history:
        history[event.chat_id] = deque(initial_prompts, maxlen=max_history)

    if kwargs.get("add_reply") is not None:
        history[event.chat_id].append(
            {
                "role": "assistant",
                "content": kwargs.get("add_reply").raw_text,
            }
        )

    history[event.chat_id].append(
        {
            "role": "user",
            "content": remove_command(event.raw_text),
        }
    )

    messages = messages + [i for i in history[event.chat_id]]

    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=max_tokens,
    )

    message = response["choices"][0]["message"]["content"]

    # Avoid appending unwanted text to history
    no_record = False
    for text_filter in text_filters:
        if text_filter in message:
            no_record = True
            break

    if no_record:
        history[event.chat_id].pop()
    else:
        history[event.chat_id].append(
            {
                "role": "assistant",
                "content": message,
            }
        )

    return message

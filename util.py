import os
import re
import openai
from collections import deque
from prompts import system_prompt, initial_prompts

max_history = int(os.getenv("MAX_HISTORY", 10))
max_tokens = int(os.getenv("MAX_TOKENS", 1024))


def remove_command(text):
    return re.sub(r"^/\S*", "", text).strip()


async def process_message(event, history):
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
    ]

    if event.chat_id not in history:
        history[event.chat_id] = deque(initial_prompts, maxlen=max_history)

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

    history[event.chat_id].append(
        {
            "role": "assistant",
            "content": message,
        }
    )

    return message

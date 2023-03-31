import os
import re
import logging
import openai
import prompts
from collections import deque
from arisbot import db

max_history = int(os.getenv("MAX_HISTORY", 10))
max_input_length = int(os.getenv("MAX_INPUT_LENGTH", 100))
max_output_length = int(os.getenv("MAX_OUTPUT_LENGTH", 500))


def remove_command(text):
    return re.sub(r"^/\S*", "", text).strip()


async def process_message(event, history, **kwargs):
    # Reset clearing chat history counter
    if kwargs.get("auto_clear") is not None:
        kwargs.get("auto_clear").pop(event.chat_id, kwargs.get("auto_clear"))

    messages = [
        {
            "role": "system",
            "content": prompts.system_prompt,
        },
    ]

    # Avoid appending unwanted text into history
    no_record = False
    no_record_reason = None

    if event.chat_id not in history:
        history[event.chat_id] = deque(prompts.initial_prompts, maxlen=max_history)

    # Process replied message
    if kwargs.get("add_reply") is not None:
        reply_text = kwargs.get("add_reply").raw_text
        history[event.chat_id].append(
            {
                "role": "assistant",
                "content": reply_text,
            }
        )
        if len(reply_text) > max_input_length:
            no_record = True
            no_record_reason = prompts.no_record_reason.get("reply_too_long")

    # Process user input
    input_text = remove_command(event.raw_text)
    history[event.chat_id].append(
        {
            "role": "user",
            "content": input_text,
        }
    )
    if len(input_text) > max_input_length:
        no_record = True
        no_record_reason = prompts.no_record_reason.get("input_too_long")

    messages = messages + [i for i in history[event.chat_id]]

    try:
        response = await openai.ChatCompletion.acreate(
            api_key=db.get(event.chat_id),
            model="gpt-3.5-turbo",
            messages=messages,
        )
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI Error: {e}")
        return f"{prompts.api_error}\n\n({e})"

    output_text = response["choices"][0]["message"]["content"]
    if len(output_text) > max_output_length:
        no_record = True
        no_record_reason = prompts.no_record_reason.get("output_too_long")
    else:
        for text_filter in prompts.text_filters:
            if text_filter in output_text:
                no_record = True
                no_record_reason = prompts.no_record_reason.get("filtered")
                break

    try:
        if no_record:
            history[event.chat_id].pop()
            if kwargs.get("add_reply") is not None:
                history[event.chat_id].pop()

            output_text = prompts.no_record.format(output_text, no_record_reason)
        else:
            history[event.chat_id].append(
                {
                    "role": "assistant",
                    "content": output_text,
                }
            )
    # history[event.chat_id] could be cleared during awaiting
    except KeyError as e:
        logging.warning(
            f"KeyError: {e}, history could have been cleared during awaiting"
        )

    return output_text

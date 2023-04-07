import os
import re
import logging
import openai
import prompts
import asyncio
from collections import deque

default_api_key = os.getenv("OPENAI_API_KEY")
max_history = int(os.getenv("MAX_HISTORY", 10))
max_input_length = int(os.getenv("MAX_INPUT_LENGTH", 100))
max_output_length = int(os.getenv("MAX_OUTPUT_LENGTH", 500))
auto_clear_count = int(os.getenv("AUTO_CLEAR_COUNT", 0))
flood_control_delay = int(os.getenv("FLOOD_CONTROL_DELAY"))


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
    db = kwargs.get("db")
    retry = kwargs.get("retry")
    history = kwargs.get("history")
    userlist = kwargs.get("userlist")
    whitelist = kwargs.get("whitelist")
    add_reply = kwargs.get("add_reply")
    auto_clear = kwargs.get("auto_clear")
    backup_key = kwargs.get("backup_key")
    flood_ctrl = kwargs.get("flood_ctrl")

    # Reset clearing chat history counter
    if auto_clear:
        auto_clear.pop(event.chat_id, auto_clear)

    using_prompt = prompts.system_prompt
    if retry:
        using_prompt = prompts.backup_prompt

    messages = [
        {
            "role": "system",
            "content": using_prompt,
        },
    ]

    # Avoid appending unwanted text into history
    no_record = False
    no_record_reason = None

    if event.chat_id not in history:
        history[event.chat_id] = deque(prompts.initial_prompts, maxlen=max_history)

    # Process replied message
    if not retry and add_reply:
        history[event.chat_id].append(add_reply)
        if len(add_reply.get("content")) > max_input_length:
            no_record = True
            no_record_reason = prompts.no_record_reason.get("reply_too_long")

    # Process user input
    if not retry:
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

    # Send API request
    try:
        api_key = (
            backup_key
            or db.get(event.chat_id)
            or event.chat_id in whitelist
            and default_api_key
            or None
        )
        response = await openai.ChatCompletion.acreate(
            api_key=api_key,
            model="gpt-3.5-turbo",
            messages=messages,
        )
    except openai.error.AuthenticationError as e:
        db_id = backup_key and event.sender_id or event.chat_id
        db.delete(db_id)
        userlist.remove(db_id)
        return f"{prompts.api_error}\n\n({e})"
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI Error: {e}")
        return f"{prompts.api_error}\n\n({e})"

    output_text = response["choices"][0]["message"]["content"]

    # Flood control
    if flood_ctrl and event.sender_id is not None:
        try:
            token_used = response["usage"]["completion_tokens"]
            if event.sender_id not in flood_ctrl[event.chat_id]:
                flood_ctrl[event.chat_id][event.sender_id] = 0
            flood_ctrl[event.chat_id][event.sender_id] += token_used

            async def clear_flood_control_counter():
                await asyncio.sleep(flood_control_delay)
                try:
                    flood_ctrl[event.chat_id][event.sender_id] = max(
                        0, flood_ctrl[event.chat_id][event.sender_id] - token_used
                    )
                except KeyError as e:
                    logging.warning(
                        f"KeyError: {e}, flood_ctrl might be deactivated during sleeping"
                    )

            asyncio.create_task(clear_flood_control_counter())
        except KeyError as e:
            logging.warning(
                f"KeyError: {e}, flood_ctrl might be deactivated during awaiting"
            )

    # Post-process
    if len(output_text) > max_output_length:
        no_record = True
        no_record_reason = prompts.no_record_reason.get("output_too_long")
    else:
        for text_filter in prompts.text_filters:
            if text_filter in output_text:
                if not retry:
                    return await process_message(
                        event,
                        db=db,
                        retry=True,
                        history=history,
                        userlist=userlist,
                        whitelist=whitelist,
                        add_reply=add_reply,
                        auto_clear=auto_clear,
                        backup_key=backup_key,
                        flood_ctrl=flood_ctrl,
                    )
                else:
                    no_record = True
                    no_record_reason = prompts.no_record_reason.get("filtered")
                    break

    # Output
    try:
        if no_record:
            history[event.chat_id].pop()
            if add_reply:
                history[event.chat_id].pop()

            output_text = prompts.no_record.format(output_text, no_record_reason)
        else:
            history[event.chat_id].append(
                {
                    "role": "assistant",
                    "content": output_text,
                }
            )

            if retry:
                output_text = prompts.profanity_warn.format(output_text)

        if backup_key:
            output_text = prompts.backup_key_used.format(output_text)
    except KeyError as e:
        logging.warning(f"KeyError: {e}, history might be cleared during awaiting")

    return output_text

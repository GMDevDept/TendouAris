# https://github.com/acheong08/Bard

import re
import asyncio
import logging
from scripts import gvars, strings, util
from scripts.types import ModelOutput, Photo
from Bard import AsyncChatbot


async def process_message_bard(
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> ModelOutput:
    access_check = util.access_scope_filter(gvars.scope_bard, chatdata.chat_id)
    if not access_check:
        return ModelOutput(
            text=f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )

    preset = model_args.get("preset", "default")

    if not chatdata.bard_chatbot:
        try:
            chatdata.bard_chatbot = await AsyncChatbot.create(
                gvars.bard_1psid, gvars.bard_1psidts
            )
        except Exception as e:
            logging.error(
                f"Error happened when creating bard_chatbot in chat {chatdata.chat_id}: {e}"
            )
            return ModelOutput(
                text=f"{strings.api_error}\n\nError Message:\n`{strings.bard_session_creation_failed}: {str(e)[:100]}`"
            )
    elif "bard" in chatdata.concurrent_lock:
        return ModelOutput(text=strings.concurrent_locked)
    elif chatdata.bard_clear_task is not None:
        chatdata.bard_clear_task.cancel()
        chatdata.bard_clear_task = None

    input_text = model_input.get("text") or "Hi"  # Bard does not accept empty string
    if input_text.startswith("爱丽丝"):
        input_text = input_text.replace("爱丽丝", "Bard", 1)

    chatdata.concurrent_lock.add("bard")
    try:
        if preset == "default":
            response = await chatdata.bard_chatbot.ask(message=input_text)
    except Exception as e:
        logging.error(
            f"Error happened when calling bard_chatbot.ask in chat {chatdata.chat_id}: {e}"
        )
        return ModelOutput(
            text=f"{strings.api_error}\n\nError Message:\n`{str(e)[:100]}`\n\n{strings.try_reset}"
        )
    finally:
        chatdata.concurrent_lock.discard("bard")

    output_text = response["content"]
    output_photos = response["images"]
    if output_photos:
        output_text = re.sub(r"\n\[.*\]", "", output_text)
        output_photos = [Photo(url=url) for url in output_photos]

    if gvars.bard_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.bard_chatbot_close_delay)
            chatdata.bard_chatbot = None

        chatdata.bard_clear_task = asyncio.create_task(scheduled_auto_close())

    return ModelOutput(text=output_text, photos=output_photos)

# https://ai.google.dev/tutorials/python_quickstart

import asyncio
import logging

from loguru import logger
from pyrogram import Client
from google.ai import generativelanguage as glm

from scripts import gvars, strings, util, prompts
from scripts.types import ModelOutput


async def process_message_gemini(
    client: Client,
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> ModelOutput:
    access_check = util.access_scope_filter(gvars.scope_gemini, chatdata.chat_id)
    if not access_check:
        return ModelOutput(
            text=f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )

    if not chatdata.gemini_session:
        try:
            new_chat = await gvars.gemini_client.start_chat(history=[])
            chatdata.gemini_session = new_chat
        except Exception as e:
            logging.error(
                f"Error happened when creating gemini chat session in chat {chatdata.chat_id}: {e}"
            )
            return ModelOutput(
                text=f"{strings.api_error}\n\nError Message:\n`{strings.gemini_chatbot_creation_failed}: {e}`"
            )
    elif "gemini" in chatdata.concurrent_lock:
        return ModelOutput(text=strings.concurrent_locked)
    elif chatdata.gemini_clear_task is not None:
        chatdata.gemini_clear_task.cancel()
        chatdata.gemini_clear_task = None

    input_text = model_input.get("text") or "Hi"  # Gemini does not accept empty string
    if model_args.get("preset") != "aris" and input_text.startswith("爱丽丝"):
        input_text = input_text.replace("爱丽丝", "Gemini", 1)

    chatdata.concurrent_lock.add("gemini")
    try:
        response = await chatdata.gemini_session.send_message_async(input_text)
    except Exception as e:
        logging.error(
            f"Error happened when calling gemini_chatbot.send_message_async in chat {chatdata.chat_id}: {e}"
        )
        return ModelOutput(
            text=f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.try_reset}"
        )
    finally:
        chatdata.concurrent_lock.discard("gemini")

    output_text = response.text.strip()

    if gvars.gemini_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.gemini_chatbot_close_delay)
            if chatdata.gemini_session is not None:
                chatdata.gemini_session = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_inactivity.format("gemini"),
                )

        chatdata.gemini_clear_task = asyncio.create_task(scheduled_auto_close())

    return ModelOutput(text=output_text)

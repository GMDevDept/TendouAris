# https://github.com/acheong08/EdgeGPT

import re
import asyncio
import logging
from scripts import gvars, strings, util
from async_bing_client import ConversationStyle
from scripts.types import ModelInput, ModelOutput, Image


async def process_message_bing(
    chatdata,  # ChatData
    model_args: dict,
    model_input: ModelInput,
) -> ModelOutput:
    access_check = util.access_scope_filter(gvars.scope_bing, chatdata.chat_id)
    if not access_check:
        return ModelOutput(
            text=f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )

    style = model_args.get("style", "creative")
    match style:
        case "creative":
            conversation_style = ConversationStyle.Creative
        case "balanced":
            conversation_style = ConversationStyle.Balanced
        case "precise":
            conversation_style = ConversationStyle.Precise
        case _:
            return ModelOutput(text=f"Unknown style: {style}")

    if not chatdata.bing_chatbot:
        try:
            chatdata.bing_chatbot = await gvars.bing_client.create_chat()
        except Exception as e:
            logging.error(
                f"Error happened when creating bing_chatbot in chat {chatdata.chat_id}: {e}"
            )
            return ModelOutput(
                text=f"{strings.api_error}\n\nError Message:\n`{strings.bing_chatbot_creation_failed}: {str(e)[:100]}`"
            )
    elif "bing" in chatdata.concurrent_lock:
        return ModelOutput(text=strings.concurrent_locked)
    elif chatdata.bing_clear_task is not None:
        chatdata.bing_clear_task.cancel()
        chatdata.bing_clear_task = None

    input_text = model_input.text
    if input_text.startswith("爱丽丝"):
        input_text = input_text.replace("爱丽丝", "Bing", 1)

    chatdata.concurrent_lock.add("bing")
    try:
        response = ""
        async for text in gvars.bing_client.ask_stream(
            input_text,
            chat=chatdata.bing_chatbot,
            conversation_style=conversation_style,
        ):
            response += text
    except Exception as e:
        logging.error(
            f"Error happened when calling bing_chatbot.ask in chat {chatdata.chat_id}: {e}"
        )
        return ModelOutput(
            text=f"{strings.api_error}\n\nError Message:\n`{str(e)[:100]}`\n\n{strings.try_reset}"
        )
    finally:
        chatdata.concurrent_lock.discard("bing")

    output_text = response.strip()
    output_images = re.search(r"\nDrew images:  \n(.*?)\n\n", response, re.DOTALL)
    if output_images:
        output_text = re.sub(
            r"Drew images:  \n.*?\n\n", "", output_text, flags=re.DOTALL
        )
        output_images = [
            Image(url=i)
            for i in re.findall(r"https?://[^\s\)]+", output_images.group(1))
        ]

    if gvars.bing_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.bing_chatbot_close_delay)
            chatdata.bing_chatbot = None

        chatdata.bing_clear_task = asyncio.create_task(scheduled_auto_close())

    return ModelOutput(text=output_text, images=output_images)

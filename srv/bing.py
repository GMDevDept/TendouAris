# https://github.com/acheong08/EdgeGPT

import re
import asyncio
import logging
from scripts import gvars, strings, util
from async_bing_client import Bing_Client, ConversationStyle
from pyrogram import Client


async def process_message_bing(
    client: Client,
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> dict:
    access_check = util.access_scope_filter(gvars.scope_bing, chatdata.chat_id)
    if not access_check:
        return {
            "text": f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        }

    style = model_args.get("style", "creative")
    match style:
        case "creative":
            conversation_style = ConversationStyle.Creative
        case "balanced":
            conversation_style = ConversationStyle.Balanced
        case "precise":
            conversation_style = ConversationStyle.Precise
        case _:
            return {"text": f"Unknown style: {style}"}

    if not chatdata.bing_chatbot:
        try:
            chatdata.bing_chatbot = Bing_Client(cookie="srv/bing_cookies.json")
        except Exception as e:
            logging.error(
                f"Error happened when creating bing_chatbot in chat {chatdata.chat_id}: {e}"
            )
            return {
                "text": f"{strings.api_error}\n\nError Message:\n`{strings.bing_chatbot_creation_failed}: {e}`"
            }
    elif "bing" in chatdata.concurrent_lock:
        return {"text": strings.concurrent_locked}
    elif chatdata.bing_clear_task is not None:
        chatdata.bing_clear_task.cancel()
        chatdata.bing_clear_task = None

    input_text = model_input.get("text")
    if input_text.startswith("爱丽丝"):
        input_text = input_text.replace("爱丽丝", "Bing", 1)

    chatdata.concurrent_lock.add("bing")
    try:
        response = await chatdata.bing_chatbot.ask(
            prompt=input_text,
            conversation_style=conversation_style,
            simplify_response=True,
        )
    except Exception as e:
        logging.error(
            f"Error happened when calling bing_chatbot.ask in chat {chatdata.chat_id}: {e}"
        )
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.try_reset}"
        }
    finally:
        chatdata.concurrent_lock.discard("bing")

    output_text = response["text"].strip()
    sources = response.get("sources_text").strip()
    if sources and sources != output_text:
        output_text = re.sub(r"\[\^(\d+)\^\]", r"[\1]", output_text)
        sources = re.sub(r"\s(\[\d+\.)", r"\n\1", sources)
        output_text = f"{output_text}\n\n{sources}"

    if gvars.bing_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.bing_chatbot_close_delay)
            if chatdata.bing_chatbot is not None:
                await chatdata.bing_chatbot.close()
                chatdata.bing_chatbot = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_inactivity.format("Bing"),
                )

        chatdata.bing_clear_task = asyncio.create_task(scheduled_auto_close())

    return {"text": output_text}

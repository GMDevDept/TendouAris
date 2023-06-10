# https://github.com/acheong08/Bard

import re
import json
import asyncio
import logging
import prompts
from typing import Optional, Union
from scripts import gvars, strings, util
from Bard import AsyncChatbot
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaDocument
from pyrogram.errors import RPCError


async def process_message_bard(
    client: Client,
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> dict:
    access_check = util.access_scope_filter(gvars.scope_bard, chatdata.chat_id)
    if not access_check:
        return {
            "text": f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        }

    preset = model_args.get("preset", "default")

    if not chatdata.bard_chatbot:
        try:
            chatdata.bard_chatbot = await AsyncChatbot.create(gvars.google_bard_cookie)
        except Exception as e:
            return {
                "text": f"{strings.api_error}\n\nError Message:\n`{strings.bard_session_creation_failed}: {e}`"
            }
    elif chatdata.bard_blocked:
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{strings.chat_concurrent_blocked}`"
        }
    elif chatdata.bard_clear_task is not None:
        chatdata.bard_clear_task.cancel()
        chatdata.bard_clear_task = None

    input_text = model_input.get("text")
    if input_text.startswith("爱丽丝"):
        input_text = input_text.replace("爱丽丝", "Bard", 1)
    if preset == "cn":
        input_text = prompts.bard_cn_prompt.format(input_text)

    chatdata.bard_blocked = True
    try:
        response = await chatdata.bard_chatbot.ask(
            message=input_text or " "
        )  # Bard does not accept empty string
    except Exception as e:
        logging.warning(
            f"Error happened when calling bard_chatbot.ask in chat {chatdata.chat_id}: {e}"
        )
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.try_reset}"
        }
    finally:
        chatdata.bard_blocked = None

    output_text = response["content"] or None
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

    output_photo: Optional[list(Union[InputMediaPhoto, InputMediaDocument])] = None
    send_text_seperately = None
    raw_photos = response.get("images")  # set, {link1, link2}
    if raw_photos:
        if len(raw_photos) > 0:
            output_text = re.sub(r"\n\[.*\]", "", output_text)
            if len(output_text) >= 1024:  # Max caption length limit set by Telegram
                send_text_seperately = True

            try:
                output_photo = [
                    InputMediaPhoto(
                        photo,
                        caption=len(output_text) < 1024
                        and i == len(raw_photos) - 1
                        and output_text
                        or "",
                    )
                    for i, photo in enumerate(raw_photos)
                ]
            except RPCError:
                output_photo = [
                    InputMediaDocument(
                        photo,
                        caption=len(output_text) < 1024
                        and i == len(raw_photos) - 1
                        and output_text
                        or "",
                    )
                    for i, photo in enumerate(raw_photos)
                ]
            except Exception as e:
                output_photo = None
                link_to_raw_photos = " ".join(
                    [f"[{i+1}]({url})" for i, url in enumerate(raw_photos)]
                )
                output_text = output_text + "\n\n" + {e} + "\n" + link_to_raw_photos

    if gvars.bard_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.bard_chatbot_close_delay)
            if chatdata.bard_chatbot is not None:
                chatdata.bard_chatbot = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_inactivity.format("Bard"),
                )

        chatdata.bard_clear_task = asyncio.create_task(scheduled_auto_close())

    return {
        "text": output_text,
        "photo": output_photo,
        "send_text_seperately": send_text_seperately,
    }

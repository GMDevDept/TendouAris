# https://github.com/acheong08/Bard

import re
import json
import asyncio
import logging
from scripts import gvars, strings, util, prompts
from Bard import AsyncChatbot
from pyrogram import Client


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
            logging.error(
                f"Error happened when creating bard_chatbot in chat {chatdata.chat_id}: {e}"
            )
            return {
                "text": f"{strings.api_error}\n\nError Message:\n`{strings.bard_session_creation_failed}: {e}`"
            }
    elif "bard" in chatdata.concurrent_lock:
        return {"text": strings.concurrent_locked}
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
        elif preset == "cn":
            input_text = prompts.bard_cn_input_prompt.format(input_text)
            pre_response = await chatdata.bard_chatbot.ask(message=input_text)
            try:
                # Match json object in the output text
                output_json = re.match(
                    r".*?({.*}).*", pre_response["content"], re.DOTALL
                ).group(1)
                output_dict = json.loads(output_json)
                input_text_final = output_dict["en_translation"]
            except (AttributeError, json.JSONDecodeError, KeyError):
                # Handle cases where the regular expression pattern does not match anything
                # or the resulting substring is not a valid JSON object
                # or the JSON object does not contain the key "en_translation"
                input_text_final = input_text  # Fallback to the original input text
            except Exception as e:
                logging.error(
                    f"Error happened when handling bard cn input in chat {chatdata.chat_id}: {e}"
                )
                return {"text": f"{strings.api_error}\n\nError Message:\n`{e}`"}

            response = await chatdata.bard_chatbot.ask(message=input_text_final)
    except Exception as e:
        logging.error(
            f"Error happened when calling bard_chatbot.ask in chat {chatdata.chat_id}: {e}"
        )
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.try_reset}"
        }
    finally:
        chatdata.concurrent_lock.discard("bard")

    output_text = response["content"]
    output_photo = response["images"]
    if output_photo:
        output_text = re.sub(r"\n\[.*\]", "", output_text)

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
    }

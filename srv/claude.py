# https://github.com/canxin121/Async-Claude-Client/tree/main

import asyncio
import logging
from scripts import gvars, strings, util, prompts
from async_claude_client import ClaudeAiClient
from pyrogram import Client


async def process_message_claude(
    client: Client,
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> dict:
    access_check = util.access_scope_filter(gvars.scope_claude, chatdata.chat_id)
    if not access_check:
        return {
            "text": f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        }

    if not chatdata.claude_chatbot:
        try:
            chatdata.claude_chatbot = await ClaudeAiClient(
                cookie="srv/claude_cookies.json"
            ).init()
            new_chat = await chatdata.claude_chatbot.create_new_chat()
            chatdata.claude_uuid = new_chat["uuid"]

            if model_args.get("preset") == "aris":
                async for _ in chatdata.claude_chatbot.ask_stream(
                    prompts.aris_preset_template_claude, chatdata.claude_uuid
                ):
                    pass
        except Exception as e:
            logging.error(
                f"Error happened when creating claude_chatbot in chat {chatdata.chat_id}: {e}"
            )
            return {
                "text": f"{strings.api_error}\n\nError Message:\n`{strings.claude_chatbot_creation_failed}: {e}`"
            }
    elif "claude" in chatdata.concurrent_lock:
        return {"text": strings.concurrent_locked}
    elif chatdata.claude_clear_task is not None:
        chatdata.claude_clear_task.cancel()
        chatdata.claude_clear_task = None

    input_text = model_input.get("text") or "Hi"  # Claude does not accept empty string
    if model_args.get("preset") != "aris" and input_text.startswith("爱丽丝"):
        input_text = input_text.replace("爱丽丝", "Claude", 1)

    chatdata.concurrent_lock.add("claude")
    try:
        response = ""
        async for text in chatdata.claude_chatbot.ask_stream(
            input_text, chatdata.claude_uuid
        ):
            response += text

        if response == "":
            return {
                "text": f"{strings.api_error}\n\nError Message:\n`{strings.claude_api_limit_reached}"
            }
    except Exception as e:
        logging.error(
            f"Error happened when calling claude_chatbot.ask_stream in chat {chatdata.chat_id}: {e}"
        )
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.try_reset}"
        }
    finally:
        chatdata.concurrent_lock.discard("claude")

    output_text = response.strip()

    if gvars.claude_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.claude_chatbot_close_delay)
            if chatdata.claude_chatbot is not None:
                chatdata.claude_chatbot = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_inactivity.format("Claude"),
                )

        chatdata.claude_clear_task = asyncio.create_task(scheduled_auto_close())

    return {"text": output_text}

# https://github.com/acheong08/EdgeGPT

import re
import asyncio
import logging
from scripts import gvars, strings
from EdgeGPT import Chatbot, ConversationStyle, NotAllowedToAccess


async def process_message_bing(
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> dict:
    style = model_args.get("style", "creative")
    match style:
        case "creative":
            conversation_style = ConversationStyle.creative
        case "balanced":
            conversation_style = ConversationStyle.balanced
        case "precise":
            conversation_style = ConversationStyle.precise
        case _:
            return {"text": f"Unknown style: {style}"}

    if not chatdata.bing_chatbot:
        try:
            chatdata.bing_chatbot = await Chatbot.create()
        except NotAllowedToAccess:
            return {
                "text": f"{strings.api_error}\n\nError Message:\n`{strings.bing_chat_creation_failed}`"
            }
    elif chatdata.bing_blocked:
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{strings.chat_concurrent_blocked}`"
        }
    elif chatdata.bing_clear_task is not None:
        chatdata.bing_clear_task.cancel()
        chatdata.bing_clear_task = None

    input_text = model_input.get("text")
    if input_text.startswith("爱丽丝"):
        input_text = input_text.replace("爱丽丝", "Bing", 1)

    chatdata.bing_blocked = True
    try:
        response = await chatdata.bing_chatbot.ask(
            prompt=input_text,
            conversation_style=conversation_style,
        )
    except Exception as e:
        logging.error(f"Error happened when calling bing_chatbot.ask: {e}")
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.try_reset}"
        }
    finally:
        chatdata.bing_blocked = None

    output_text = response["item"]["messages"][1]["text"]
    sourceAttributions = response["item"]["messages"][1]["sourceAttributions"]
    if len(sourceAttributions) > 0:
        output_text = re.sub(r"\[\^(\d+)\^\]", r"[\1]", output_text)
        reference_links = "\n".join(
            [
                f"[[{i+1}] {sourceAttributions[i]['providerDisplayName']}]({sourceAttributions[i]['seeMoreUrl']})"
                for i in range(len(sourceAttributions))
            ]
        )
        reference_text = f"\n\nReferences:\n{reference_links}"
        output_text = output_text + reference_text

    if gvars.bing_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.bing_chatbot_close_delay)
            if chatdata.bing_chatbot is not None:
                await chatdata.bing_chatbot.close()
                chatdata.bing_chatbot = None
                logging.info(
                    f"Bing chatbot for chat {chatdata.chat_id} has been closed due to inactivity"
                )

        chatdata.bing_clear_task = asyncio.create_task(scheduled_auto_close())

    return {"text": output_text}

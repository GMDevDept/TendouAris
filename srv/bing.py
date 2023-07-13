# https://github.com/acheong08/EdgeGPT

import re
import json
import asyncio
import logging
from scripts import gvars, strings, util
from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle
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
        except Exception:
            try:
                cookies = json.loads(
                    open("srv/bing_cookies_fallback.json", encoding="utf-8").read()
                )
                chatdata.bing_chatbot = await Chatbot.create(cookies=cookies)
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

    output_text = response["text"]
    sources = response.get("sources_text")
    if sources and len(sources) > 0:
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


{
    "text": "What can I help you with? Please let me know if you have any questions or if there is anything specific you would like me to help you with.",
    "author": "bot",
    "sources": '[1]: https://hinative.com/questions/734671 "What is the difference between \\"what can I help you with. - HiNative"\n[2]: https://redkiwiapp.com/ja/questions/pNh4MPA6dT9hGQMMPtsy "What can I help you with?とHow can I help you?に違いはありますか。"\n[3]: https://grammarhow.com/better-ways-to-say-how-can-i-help-you/ "10 Better Ways to Say “How Can I Help You?” - Grammarhow"\n[4]: https://support.microsoft.com/en-us/windows/what-can-we-help-you-do-today-01d49822-8ee3-89cd-7069-18103116ca07 "What can we help you do today? - Microsoft Support"\n[5]: https://www.verywellmind.com/i-need-help-what-to-do-if-you-feel-this-way-5235679 "I Need Help: What to Do If You Feel This Way - Verywell Mind"\n[6]: https://www.verywellmind.com/please-help-me-5104729 "Please Help Me: What to Do When You Need Help - Verywell Mind"\n\nWhat can I help you with? Please let me know if you have any questions or if there is anything specific you would like me to help you with.\n',
    "sources_text": "Learn more: [1. hinative.com](https://hinative.com/questions/734671) [2. redkiwiapp.com](https://redkiwiapp.com/ja/questions/pNh4MPA6dT9hGQMMPtsy) [3. grammarhow.com](https://grammarhow.com/better-ways-to-say-how-can-i-help-you/) [4. support.microsoft.com](https://support.microsoft.com/en-us/windows/what-can-we-help-you-do-today-01d49822-8ee3-89cd-7069-18103116ca07) [5. www.verywellmind.com](https://www.verywellmind.com/i-need-help-what-to-do-if-you-feel-this-way-5235679) [6. www.verywellmind.com](https://www.verywellmind.com/please-help-me-5104729)",
    "suggestions": [],
    "messages_left": 9,
    "max_messages": 10,
    "adaptive_text": '[1]: https://hinative.com/questions/734671 "What is the difference between \\"what can I help you with. - HiNative"\n[2]: https://redkiwiapp.com/ja/questions/pNh4MPA6dT9hGQMMPtsy "What can I help you with?とHow can I help you?に違いはありますか。"\n[3]: https://grammarhow.com/better-ways-to-say-how-can-i-help-you/ "10 Better Ways to Say “How Can I Help You?” - Grammarhow"\n[4]: https://support.microsoft.com/en-us/windows/what-can-we-help-you-do-today-01d49822-8ee3-89cd-7069-18103116ca07 "What can we help you do today? - Microsoft Support"\n[5]: https://www.verywellmind.com/i-need-help-what-to-do-if-you-feel-this-way-5235679 "I Need Help: What to Do If You Feel This Way - Verywell Mind"\n[6]: https://www.verywellmind.com/please-help-me-5104729 "Please Help Me: What to Do When You Need Help - Verywell Mind"\n\nWhat can I help you with? Please let me know if you have any questions or if there is anything specific you would like me to help you with.\n',
}

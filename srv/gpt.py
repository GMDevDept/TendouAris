import logging
import asyncio
import prompts
from pyrogram import Client
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from scripts import gvars, strings, util


async def process_message_gpt35(
    client: Client,
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> dict:
    access_check = util.access_scope_filter(gvars.scope_gpt35, chatdata.chat_id)
    if not access_check:
        return {
            "text": f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        }

    api_key = (
        chatdata.openai_api_key
        or chatdata.chat_id in gvars.whitelist
        and gvars.openai_api_key
        or model_input.get("sender_id")
        and util.load_chat(model_input.get("sender_id"))
        and util.load_chat(model_input.get("sender_id")).openai_api_key
    )
    if not api_key:
        return {"text": f"{strings.no_auth}\n\n{strings.api_key_required}"}

    # Chatbot should be reset when handling preset changing (gpt35_preset_selection_callback_handler)
    if chatdata.gpt35_chatbot is None or chatdata.gpt35_history is None:
        preset = model_args.get("preset", "aris")
        conversation_model = ChatOpenAI(
            model="gpt-3.5-turbo", temperature=1, openai_api_key=api_key
        )

        match preset:
            case "aris":
                chatdata.gpt35_chatbot = create_gpt35_aris_chatbot(
                    chatdata, conversation_model
                )
            case "default":
                chatdata.gpt35_chatbot = create_gpt35_default_chatbot(
                    chatdata, conversation_model
                )
            case _:
                return {
                    "text": f"{strings.internal_error}\n\nError message: `Invalid preset for gpt-3.5 model: {preset}`"
                }
    elif chatdata.gpt35_clear_task is not None:
        chatdata.gpt35_clear_task.cancel()
        chatdata.gpt35_clear_task = None

    input_text = model_input.get("text")
    if input_text.startswith("爱丽丝") and model_args.get("preset") != "aris":
        input_text = input_text.replace("爱丽丝", "", 1)

    try:
        response = await chatdata.gpt35_chatbot.apredict(input=input_text)
    except Exception as e:
        logging.warning(
            f"Error happened when calling gpt35_chatbot.apredict in chat {chatdata.chat_id}: {e}"
        )
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.api_key_common_errors}"
        }

    if chatdata.is_group and gvars.gpt35_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.gpt35_chatbot_close_delay)
            if chatdata.gpt35_chatbot is not None:
                chatdata.gpt35_chatbot = None
            if chatdata.gpt35_history is not None:
                chatdata.gpt35_history.clear()
                chatdata.gpt35_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_inactivity.format("GPT-3.5"),
                )

        chatdata.gpt35_clear_task = asyncio.create_task(scheduled_auto_close())

    return {"text": response}


def create_gpt35_aris_chatbot(
    chatdata, conversation_model: ChatOpenAI
) -> ConversationChain:
    aris_prompt = PromptTemplate(
        input_variables=["history", "input"], template=prompts.aris_prompt_template
    )
    summary_prompt = PromptTemplate(
        input_variables=["summary", "new_lines"],
        template=prompts.summary_prompt_template,
    )

    if not chatdata.gpt35_history:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            human_prefix="老师",
            ai_prefix="爱丽丝",
            llm=conversation_model,
            prompt=summary_prompt,
            max_token_limit=1024,
        )

    gpt35_aris_chatbot = ConversationChain(
        llm=conversation_model, prompt=aris_prompt, memory=chatdata.gpt35_history
    )

    return gpt35_aris_chatbot


def create_gpt35_default_chatbot(
    chatdata, conversation_model: ChatOpenAI
) -> ConversationChain:
    if not chatdata.gpt35_history:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            llm=conversation_model,
            max_token_limit=2048,
        )

    gpt35_default_chatbot = ConversationChain(
        llm=conversation_model, memory=chatdata.gpt35_history
    )

    return gpt35_default_chatbot

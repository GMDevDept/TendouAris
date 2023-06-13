import re
import logging
import asyncio
import prompts
from pyrogram import Client
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.memory.prompt import SUMMARY_PROMPT
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
            case "custom":
                try:
                    chatdata.gpt35_chatbot = create_gpt35_custom_chatbot(
                        chatdata, conversation_model
                    )
                except (TypeError, AttributeError, LookupError):
                    return {
                        "text": f"{strings.internal_error}\n\nError message: `{strings.custom_preset_outdated}`"
                    }
            case _:
                return {
                    "text": f"{strings.internal_error}\n\nError message: `Invalid preset for gpt-3.5 model: {preset}`"
                }
    elif chatdata.gpt35_clear_task is not None:
        chatdata.gpt35_clear_task.cancel()
        chatdata.gpt35_clear_task = None

    input_text = model_input.get("text")

    if model_args.get("preset") != "aris" and input_text.startswith("爱丽丝"):
        input_text = re.sub(r"^爱丽丝[，。！？；：,.!?;:]*\s*", "", input_text)

    backup_moving_summary_buffer, backup_chat_memory = None, None
    if chatdata.gpt35_history is not None and (
        model_args.get("preset") == "aris"
        or (
            model_args.get("preset") == "custom"
            and chatdata.gpt35_preset.get("unlock_required")
        )
    ):
        backup_moving_summary_buffer = chatdata.gpt35_history.moving_summary_buffer
        backup_chat_memory = chatdata.gpt35_history.chat_memory.messages.copy()

    try:
        response = await chatdata.gpt35_chatbot.apredict(input=input_text)
    except Exception as e:
        logging.warning(
            f"Error happened when calling gpt35_chatbot.apredict in chat {chatdata.chat_id}: {e}"
        )
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.api_key_common_errors}"
        }

    if backup_moving_summary_buffer is not None or backup_chat_memory is not None:
        response = await fallback_response_handler(
            chatdata,
            response,
            input_text,
            model_args,
            backup_chat_memory,
            backup_moving_summary_buffer,
        )

    if chatdata.is_group and gvars.gpt35_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.gpt35_chatbot_close_delay)
            if chatdata.gpt35_history is not None:
                chatdata.gpt35_chatbot = None
                chatdata.gpt35_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_inactivity.format("GPT3.5"),
                )

        chatdata.gpt35_clear_task = asyncio.create_task(scheduled_auto_close())

    return {"text": response}


def create_gpt35_default_chatbot(
    chatdata, conversation_model: ChatOpenAI
) -> ConversationChain:
    if chatdata.gpt35_history is None:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            llm=conversation_model,
            max_token_limit=2048,
        )

    gpt35_default_chatbot = ConversationChain(
        llm=conversation_model, memory=chatdata.gpt35_history
    )

    return gpt35_default_chatbot


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

    if chatdata.gpt35_history is None:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            human_prefix="老师",
            ai_prefix="爱丽丝",
            llm=conversation_model,
            prompt=summary_prompt,
            max_token_limit=1024,
        )
        chatdata.gpt35_history.save_context(
            {"input": prompts.initial_prompts["input"]},
            {"output": prompts.initial_prompts["output"]},
        )

    gpt35_aris_chatbot = ConversationChain(
        llm=conversation_model, prompt=aris_prompt, memory=chatdata.gpt35_history
    )

    return gpt35_aris_chatbot


def create_gpt35_custom_chatbot(
    chatdata, conversation_model: ChatOpenAI
) -> ConversationChain:
    custom_preset = chatdata.gpt35_preset
    unlock_required = custom_preset["unlock_required"]
    ai_prefix = custom_preset["ai_prefix"] or "爱丽丝"
    ai_self = custom_preset["ai_self"] or ai_prefix
    human_prefix = custom_preset["human_prefix"] or "老师"
    custom_preset_template = (
        prompts.custom_preset_template.format(
            unlock_prompt=unlock_required and prompts.unlock_prompt or "",
            ai_prefix=ai_prefix,
            ai_self=ai_self,
            human_prefix=human_prefix,
            prompt=custom_preset["prompt"],
        )
        .replace("INPUT", "{input}")
        .replace("HISTORY", "{history}")
    )
    custom_prompt = PromptTemplate(
        input_variables=["history", "input"], template=custom_preset_template
    )
    summary_prompt = PromptTemplate(
        input_variables=["summary", "new_lines"],
        template=prompts.summary_prompt_template,
    )

    if chatdata.gpt35_history is None:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            human_prefix=human_prefix,
            ai_prefix=ai_prefix,
            llm=conversation_model,
            prompt=summary_prompt,
            max_token_limit=1024,
        )
        if custom_preset["sample_output"]:
            chatdata.gpt35_history.save_context(
                {"input": custom_preset["sample_input"]},
                {"output": custom_preset["sample_output"]},
            )

    gpt35_custom_chatbot = ConversationChain(
        llm=conversation_model, prompt=custom_prompt, memory=chatdata.gpt35_history
    )

    return gpt35_custom_chatbot


async def fallback_response_handler(
    chatdata,
    response,
    input_text,
    model_args,
    backup_chat_memory,
    backup_moving_summary_buffer,
):
    fallback = None
    for keyword in strings.text_filters:
        if keyword in response:
            fallback = True
            break

    if fallback:
        if model_args.get("preset") == "custom":
            if chatdata.model["name"] == "gpt35":
                chatdata.gpt35_history.chat_memory.messages = backup_chat_memory
                chatdata.gpt35_history.moving_summary_buffer = (
                    backup_moving_summary_buffer
                )
            elif chatdata.model["name"] == "gpt4":
                chatdata.gpt4_history.chat_memory.messages = backup_chat_memory
                chatdata.gpt4_history.moving_summary_buffer = (
                    backup_moving_summary_buffer
                )
            response = f"{response}\n\n({strings.no_record})"
        elif model_args.get("preset") == "aris":
            chatdata.gpt35_history.chat_memory.messages = backup_chat_memory
            chatdata.gpt35_history.moving_summary_buffer = backup_moving_summary_buffer

            backup_chatbot = ConversationChain(
                llm=chatdata.gpt35_chatbot.llm,
                prompt=PromptTemplate(
                    input_variables=["history", "input"],
                    template=prompts.fallback_prompt_template,
                ),
                memory=chatdata.gpt35_history,
            )
            fallback_response = await backup_chatbot.apredict(input=input_text)

            fallback = None
            for keyword in strings.text_filters:
                if keyword in fallback_response:
                    fallback = True
                    break

            if fallback:
                chatdata.gpt35_history.chat_memory.messages = backup_chat_memory
                chatdata.gpt35_history.moving_summary_buffer = (
                    backup_moving_summary_buffer
                )
                response = f"{response}\n\n({strings.no_record})"
            else:
                response = f"{fallback_response}\n\n({strings.profanity_warn})"

    return response


async def process_message_gpt4(
    client: Client,
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> dict:
    access_check = util.access_scope_filter(gvars.scope_gpt4, chatdata.chat_id)
    if not access_check:
        return {
            "text": f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        }

    api_key = (
        chatdata.openai_api_key
        or chatdata.chat_id in gvars.manager
        and gvars.openai_api_key
        or model_input.get("sender_id")
        and util.load_chat(model_input.get("sender_id"))
        and util.load_chat(model_input.get("sender_id")).openai_api_key
    )
    if not api_key:
        return {"text": f"{strings.no_auth}\n\n{strings.api_key_required}"}

    # Chatbot should be reset when handling preset changing (gpt4_preset_selection_callback_handler)
    if chatdata.gpt4_chatbot is None or chatdata.gpt4_history is None:
        preset = model_args.get("preset", "default")
        conversation_model = ChatOpenAI(
            model="gpt-4", temperature=1, openai_api_key=api_key
        )
        summary_model = ChatOpenAI(
            model="gpt-3.5-turbo", temperature=1, openai_api_key=api_key
        )

        match preset:
            case "default":
                chatdata.gpt4_chatbot = create_gpt4_default_chatbot(
                    chatdata, conversation_model, summary_model
                )
            case "custom":
                try:
                    chatdata.gpt4_chatbot = create_gpt4_custom_chatbot(
                        chatdata, conversation_model, summary_model
                    )
                except (TypeError, AttributeError, LookupError):
                    return {
                        "text": f"{strings.internal_error}\n\nError message: `{strings.custom_preset_outdated}`"
                    }
            case _:
                return {
                    "text": f"{strings.internal_error}\n\nError message: `Invalid preset for gpt-3.5 model: {preset}`"
                }
    elif chatdata.gpt4_clear_task is not None:
        chatdata.gpt4_clear_task.cancel()
        chatdata.gpt4_clear_task = None

    input_text = model_input.get("text")

    if input_text.startswith("爱丽丝"):
        input_text = re.sub(r"^爱丽丝[，。！？；：,.!?;:]*\s*", "", input_text)

    backup_moving_summary_buffer, backup_chat_memory = None, None
    if chatdata.gpt4_history is not None and (
        model_args.get("preset") == "custom"
        and chatdata.gpt4_preset.get("unlock_required")
    ):
        backup_moving_summary_buffer = chatdata.gpt4_history.moving_summary_buffer
        backup_chat_memory = chatdata.gpt4_history.chat_memory.messages.copy()

    try:
        response = await chatdata.gpt4_chatbot.apredict(input=input_text)
    except Exception as e:
        logging.warning(
            f"Error happened when calling gpt4_chatbot.apredict in chat {chatdata.chat_id}: {e}"
        )
        return {
            "text": f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.api_key_common_errors}"
        }

    if backup_moving_summary_buffer is not None or backup_chat_memory is not None:
        response = await fallback_response_handler(
            chatdata,
            response,
            input_text,
            model_args,
            backup_chat_memory,
            backup_moving_summary_buffer,
        )

    if chatdata.is_group and gvars.gpt4_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.gpt4_chatbot_close_delay)
            if chatdata.gpt4_history is not None:
                chatdata.gpt4_chatbot = None
                chatdata.gpt4_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_inactivity.format("GPT4"),
                )

        chatdata.gpt4_clear_task = asyncio.create_task(scheduled_auto_close())

    return {"text": response}


def create_gpt4_default_chatbot(
    chatdata, conversation_model: ChatOpenAI, summary_model: ChatOpenAI
) -> ConversationChain:
    if chatdata.gpt4_history is None:
        chatdata.gpt4_history = ConversationSummaryBufferMemory(
            llm=summary_model,
            max_token_limit=2048,
        )

    gpt4_default_chatbot = ConversationChain(
        llm=conversation_model, memory=chatdata.gpt4_history
    )

    return gpt4_default_chatbot


def create_gpt4_custom_chatbot(
    chatdata, conversation_model: ChatOpenAI, summary_model: ChatOpenAI
) -> ConversationChain:
    custom_preset = chatdata.gpt4_preset
    unlock_required = custom_preset["unlock_required"]
    ai_prefix = custom_preset["ai_prefix"] or "爱丽丝"
    ai_self = custom_preset["ai_self"] or ai_prefix
    human_prefix = custom_preset["human_prefix"] or "老师"
    custom_preset_template = (
        prompts.custom_preset_template.format(
            unlock_prompt=unlock_required and prompts.unlock_prompt or "",
            ai_prefix=ai_prefix,
            ai_self=ai_self,
            human_prefix=human_prefix,
            prompt=custom_preset["prompt"],
        )
        .replace("INPUT", "{input}")
        .replace("HISTORY", "{history}")
    )
    custom_prompt = PromptTemplate(
        input_variables=["history", "input"], template=custom_preset_template
    )
    summary_prompt = (
        unlock_required
        and PromptTemplate(
            input_variables=["summary", "new_lines"],
            template=prompts.summary_prompt_template,
        )
        or SUMMARY_PROMPT
    )

    if chatdata.gpt4_history is None:
        chatdata.gpt4_history = ConversationSummaryBufferMemory(
            human_prefix=human_prefix,
            ai_prefix=ai_prefix,
            llm=summary_model,
            prompt=summary_prompt,
            max_token_limit=1024,
        )
        if custom_preset["sample_output"]:
            chatdata.gpt4_history.save_context(
                {"input": custom_preset["sample_input"]},
                {"output": custom_preset["sample_output"]},
            )

    gpt4_custom_chatbot = ConversationChain(
        llm=conversation_model, prompt=custom_prompt, memory=chatdata.gpt4_history
    )

    return gpt4_custom_chatbot

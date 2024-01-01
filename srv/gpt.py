import re
import logging
import asyncio
from pyrogram import Client
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from scripts import gvars, strings, util, prompts
from scripts.types import ModelOutput


async def process_message_gpt35(
    client: Client,
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> ModelOutput:
    access_check = util.access_scope_filter(gvars.scope_gpt35, chatdata.chat_id)
    if not access_check:
        return ModelOutput(
            text=f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )

    api_key = (
        chatdata.openai_api_key
        or chatdata.chat_id in gvars.whitelist
        and gvars.openai_api_key
        or model_input.get("sender_id")
        and util.load_chat(model_input.get("sender_id"))
        and util.load_chat(model_input.get("sender_id")).openai_api_key
    )
    if not api_key:
        return ModelOutput(text=f"{strings.no_auth}\n\n{strings.api_key_required}")

    # Chatbot should be reset when handling preset changing (gpt35_preset_selection_callback_handler)
    if chatdata.gpt35_chatbot is None or chatdata.gpt35_history is None:
        preset = model_args.get("preset", "aris")
        conversation_model = ChatOpenAI(
            model="gpt-3.5-turbo-16k", temperature=0.7, openai_api_key=api_key
        )
        summary_model = ChatOpenAI(
            model="gpt-3.5-turbo-16k", temperature=0.3, openai_api_key=api_key
        )

        match preset:
            case "aris":
                chatdata.gpt35_chatbot = create_gpt35_aris_chatbot(
                    chatdata, conversation_model, summary_model
                )
            case "default":
                chatdata.gpt35_chatbot = create_gpt35_default_chatbot(
                    chatdata, conversation_model, summary_model
                )
            case "custom":
                custom_preset = chatdata.gpt35_preset
                try:
                    chatdata.gpt35_chatbot = create_gpt35_custom_chatbot(
                        chatdata, conversation_model, summary_model, custom_preset
                    )
                except (TypeError, AttributeError, LookupError):
                    return ModelOutput(
                        text=f"{strings.internal_error}\n\nError message: `{strings.custom_preset_outdated}`"
                    )
            case "addon":
                preset_id = model_args.get("id")
                addon_preset = gvars.gpt35_addons.get(preset_id)
                try:
                    chatdata.gpt35_chatbot = create_gpt35_custom_chatbot(
                        chatdata, conversation_model, summary_model, addon_preset
                    )
                except (TypeError, AttributeError, LookupError) as e:
                    logging.error(
                        f"Error happened when loading gpt35 addon: {e}\nPreset id:{preset_id}"
                    )
                    return ModelOutput(
                        text=f"{strings.internal_error}\n\nError message: `{strings.addon_preset_invalid}\n{preset_id}: {e}`\n\n{strings.feedback}"
                    )
            case _:
                return ModelOutput(
                    text=f"{strings.internal_error}\n\nError message: `Invalid preset for gpt35 model: {preset}`"
                )
    elif "gpt35" in chatdata.concurrent_lock:
        return ModelOutput(text=strings.concurrent_locked)
    elif chatdata.gpt35_clear_task is not None:
        chatdata.gpt35_clear_task.cancel()
        chatdata.gpt35_clear_task = None

    input_text = model_input.get("text") or "Hi"  # Prevent self generated conversations
    if model_args.get("preset") != "aris" and input_text.startswith("爱丽丝"):
        if model_args.get("preset") == "custom" and chatdata.gpt35_preset.get(
            "ai_prefix"
        ):
            input_text = input_text.replace(
                "爱丽丝", chatdata.gpt35_preset.get("ai_prefix"), 1
            )
        elif model_args.get("preset") == "addon" and gvars.gpt35_addons.get(
            model_args.get("id")
        ).get("ai_prefix"):
            input_text = input_text.replace(
                "爱丽丝", gvars.gpt35_addons.get(model_args.get("id")).get("ai_prefix"), 1
            )
        else:
            input_text = re.sub(r"^爱丽丝[，。！？；：,.!?;:]*\s*", "", input_text)

    backup_moving_summary_buffer, backup_chat_memory = None, None
    if chatdata.gpt35_history is not None and (
        model_args.get("preset") == "aris"
        or (
            model_args.get("preset") == "custom"
            and chatdata.gpt35_preset.get("keyword_filter")
        )
        or (
            model_args.get("preset") == "addon"
            and gvars.gpt35_addons.get(model_args.get("id")).get("keyword_filter")
        )
    ):
        backup_moving_summary_buffer = chatdata.gpt35_history.moving_summary_buffer
        backup_chat_memory = chatdata.gpt35_history.chat_memory.messages.copy()

    chatdata.concurrent_lock.add("gpt35")
    try:
        response = await chatdata.gpt35_chatbot.apredict(input=input_text)
    except Exception as e:
        logging.error(
            f"Error happened when calling gpt35_chatbot.apredict in chat {chatdata.chat_id}: {e}"
        )
        return ModelOutput(
            text=f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.api_key_common_errors}"
        )
    finally:
        chatdata.concurrent_lock.discard("gpt35")

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
            chatdata.gpt35_chatbot = None
            chatdata.gpt35_history = None

        chatdata.gpt35_clear_task = asyncio.create_task(scheduled_auto_close())

    return ModelOutput(text=response)


def create_gpt35_default_chatbot(
    chatdata, conversation_model: ChatOpenAI, summary_model: ChatOpenAI
) -> ConversationChain:
    if chatdata.gpt35_history is None:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            llm=summary_model,
            max_token_limit=2048,
        )

    gpt35_default_chatbot = ConversationChain(
        llm=conversation_model, memory=chatdata.gpt35_history
    )

    return gpt35_default_chatbot


def create_gpt35_aris_chatbot(
    chatdata, conversation_model: ChatOpenAI, summary_model: ChatOpenAI
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
            llm=summary_model,
            prompt=summary_prompt,
            max_token_limit=2048,
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
    chatdata,
    conversation_model: ChatOpenAI,
    summary_model: ChatOpenAI,
    preset_args: dict,
) -> ConversationChain:
    unlock_required = preset_args.get("unlock_required")
    ai_prefix = preset_args.get("ai_prefix") or preset_args.get("ai_self")
    ai_prefix = ai_prefix and ai_prefix.strip()
    ai_self = preset_args.get("ai_self") or ai_prefix
    ai_self = ai_self and ai_self.strip()
    human_prefix = preset_args.get("human_prefix")
    human_prefix = human_prefix and human_prefix.strip()

    ai_rename_prompt = (
        (ai_prefix and ai_self)
        and prompts.ai_rename_prompt.format(ai_prefix=ai_prefix, ai_self=ai_self)
        or ""
    )
    human_rename_prompt = (
        human_prefix
        and prompts.human_rename_prompt.format(human_prefix=human_prefix)
        or ""
    )
    rename_prompt = (
        (ai_rename_prompt or human_rename_prompt)
        and prompts.rename_prompt.format(
            ai_rename_prompt=ai_rename_prompt, human_rename_prompt=human_rename_prompt
        )
        or ""
    )
    custom_preset_template = (
        prompts.custom_preset_template.format(
            unlock_prompt=unlock_required and prompts.unlock_prompt or "",
            rename_prompt=rename_prompt,
            system_prompt=preset_args["prompt"],
            human_prefix=human_prefix or "我",
            ai_prefix=ai_prefix or "你",
        )
        .replace("INPUT", "{input}")
        .replace("HISTORY", "{history}")
    )
    custom_prompt = PromptTemplate(
        input_variables=["history", "input"], template=custom_preset_template
    )

    if chatdata.gpt35_history is None:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            human_prefix=human_prefix or "我",
            ai_prefix=ai_prefix or "你",
            llm=summary_model,
            prompt=PromptTemplate(
                input_variables=["summary", "new_lines"],
                template=prompts.summary_prompt_template,
            ),
            max_token_limit=preset_args.get("buffer_token_limit", 2048),
        )
        if preset_args.get("sample_io"):
            for io_pair in preset_args.get("sample_io"):
                chatdata.gpt35_history.save_context(
                    {"input": io_pair["input"]}, {"output": io_pair["output"]}
                )
        elif preset_args.get("sample_output"):
            chatdata.gpt35_history.save_context(
                {"input": preset_args.get("sample_input")},
                {"output": preset_args.get("sample_output")},
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
        if model_args.get("preset") == "custom" or model_args.get("preset") == "addon":
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

            chatdata.concurrent_lock.add(chatdata.model["name"])
            try:
                fallback_response = await backup_chatbot.apredict(input=input_text)
            except Exception as e:
                logging.error(
                    f"Error happened when calling backup_chatbot.apredict in chat {chatdata.chat_id}: {e}"
                )
                return ModelOutput(
                    text=f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.api_key_common_errors}"
                )
            finally:
                chatdata.concurrent_lock.discard(chatdata.model["name"])

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
        return ModelOutput(
            text=f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )

    api_key = (
        chatdata.openai_api_key
        or chatdata.chat_id in gvars.manager
        and gvars.openai_api_key
        or model_input.get("sender_id")
        and util.load_chat(model_input.get("sender_id"))
        and util.load_chat(model_input.get("sender_id")).openai_api_key
    )
    if not api_key:
        return ModelOutput(text=f"{strings.no_auth}\n\n{strings.api_key_required}")

    # Chatbot should be reset when handling preset changing (gpt4_preset_selection_callback_handler)
    if chatdata.gpt4_chatbot is None or chatdata.gpt4_history is None:
        preset = model_args.get("preset", "default")
        conversation_model = ChatOpenAI(
            model="gpt-4-1106-preview", temperature=0.7, openai_api_key=api_key
        )
        summary_model = ChatOpenAI(
            model="gpt-3.5-turbo-16k", temperature=0.3, openai_api_key=api_key
        )

        match preset:
            case "default":
                chatdata.gpt4_chatbot = create_gpt4_default_chatbot(
                    chatdata, conversation_model, summary_model
                )
            case "custom":
                custom_preset = chatdata.gpt4_preset
                try:
                    chatdata.gpt4_chatbot = create_gpt4_custom_chatbot(
                        chatdata, conversation_model, summary_model, custom_preset
                    )
                except (TypeError, AttributeError, LookupError):
                    return ModelOutput(
                        text=f"{strings.internal_error}\n\nError message: `{strings.custom_preset_outdated}`"
                    )
            case "addon":
                preset_id = model_args.get("id")
                addon_preset = gvars.gpt4_addons.get(preset_id)
                try:
                    chatdata.gpt4_chatbot = create_gpt4_custom_chatbot(
                        chatdata, conversation_model, summary_model, addon_preset
                    )
                except (TypeError, AttributeError, LookupError) as e:
                    logging.error(
                        f"Error happened when loading gpt4 addon: {e}\nPreset id:{preset_id}"
                    )
                    return ModelOutput(
                        text=f"{strings.internal_error}\n\nError message: `{strings.addon_preset_invalid}\n{preset_id}: {e}`\n\n{strings.feedback}"
                    )
            case _:
                return ModelOutput(
                    text=f"{strings.internal_error}\n\nError message: `Invalid preset for gpt4 model: {preset}`"
                )
    elif "gpt4" in chatdata.concurrent_lock:
        return ModelOutput(text=strings.concurrent_locked)
    elif chatdata.gpt4_clear_task is not None:
        chatdata.gpt4_clear_task.cancel()
        chatdata.gpt4_clear_task = None

    input_text = model_input.get("text") or "Hi"  # Prevent self generated conversations
    if input_text.startswith("爱丽丝"):
        if model_args.get("preset") == "custom" and chatdata.gpt4_preset.get(
            "ai_prefix"
        ):
            input_text = input_text.replace(
                "爱丽丝", chatdata.gpt4_preset.get("ai_prefix"), 1
            )
        elif model_args.get("preset") == "addon" and gvars.gpt4_addons.get(
            model_args.get("id")
        ).get("ai_prefix"):
            input_text = input_text.replace(
                "爱丽丝", gvars.gpt4_addons.get(model_args.get("id")).get("ai_prefix"), 1
            )
        else:
            input_text = re.sub(r"^爱丽丝[，。！？；：,.!?;:]*\s*", "", input_text)

    backup_moving_summary_buffer, backup_chat_memory = None, None
    if chatdata.gpt4_history is not None and (
        (
            model_args.get("preset") == "custom"
            and chatdata.gpt4_preset.get("keyword_filter")
        )
        or (
            model_args.get("preset") == "addon"
            and gvars.gpt4_addons.get(model_args.get("id")).get("keyword_filter")
        )
    ):
        backup_moving_summary_buffer = chatdata.gpt4_history.moving_summary_buffer
        backup_chat_memory = chatdata.gpt4_history.chat_memory.messages.copy()

    chatdata.concurrent_lock.add("gpt4")
    try:
        response = await chatdata.gpt4_chatbot.apredict(input=input_text)
    except Exception as e:
        logging.error(
            f"Error happened when calling gpt4_chatbot.apredict in chat {chatdata.chat_id}: {e}"
        )
        return ModelOutput(
            text=f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.api_key_common_errors}"
        )
    finally:
        chatdata.concurrent_lock.discard("gpt4")

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
            chatdata.gpt4_chatbot = None
            chatdata.gpt4_history = None

        chatdata.gpt4_clear_task = asyncio.create_task(scheduled_auto_close())

    return ModelOutput(text=response)


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
    chatdata,
    conversation_model: ChatOpenAI,
    summary_model: ChatOpenAI,
    preset_args: dict,
) -> ConversationChain:
    unlock_required = preset_args.get("unlock_required")
    ai_prefix = preset_args.get("ai_prefix") or preset_args.get("ai_self")
    ai_prefix = ai_prefix and ai_prefix.strip()
    ai_self = preset_args.get("ai_self") or ai_prefix
    ai_self = ai_self and ai_self.strip()
    human_prefix = preset_args.get("human_prefix")
    human_prefix = human_prefix and human_prefix.strip()

    ai_rename_prompt = (
        (ai_prefix and ai_self)
        and prompts.ai_rename_prompt.format(ai_prefix=ai_prefix, ai_self=ai_self)
        or ""
    )
    human_rename_prompt = (
        human_prefix
        and prompts.human_rename_prompt.format(human_prefix=human_prefix)
        or ""
    )
    rename_prompt = (
        (ai_rename_prompt or human_rename_prompt)
        and prompts.rename_prompt.format(
            ai_rename_prompt=ai_rename_prompt, human_rename_prompt=human_rename_prompt
        )
        or ""
    )
    custom_preset_template = (
        prompts.custom_preset_template.format(
            unlock_prompt=unlock_required and prompts.unlock_prompt or "",
            rename_prompt=rename_prompt,
            system_prompt=preset_args["prompt"],
            human_prefix=human_prefix or "我",
            ai_prefix=ai_prefix or "你",
        )
        .replace("INPUT", "{input}")
        .replace("HISTORY", "{history}")
    )
    custom_prompt = PromptTemplate(
        input_variables=["history", "input"], template=custom_preset_template
    )

    if chatdata.gpt4_history is None:
        chatdata.gpt4_history = ConversationSummaryBufferMemory(
            human_prefix=human_prefix or "我",
            ai_prefix=ai_prefix or "你",
            llm=summary_model,
            prompt=PromptTemplate(
                input_variables=["summary", "new_lines"],
                template=prompts.summary_prompt_template,
            ),
            max_token_limit=preset_args.get("buffer_token_limit", 2048),
        )
        if preset_args.get("sample_io"):
            for io_pair in preset_args.get("sample_io"):
                chatdata.gpt4_history.save_context(
                    {"input": io_pair["input"]}, {"output": io_pair["output"]}
                )
        elif preset_args.get("sample_output"):
            chatdata.gpt4_history.save_context(
                {"input": preset_args.get("sample_input")},
                {"output": preset_args.get("sample_output")},
            )

    gpt4_custom_chatbot = ConversationChain(
        llm=conversation_model, prompt=custom_prompt, memory=chatdata.gpt4_history
    )

    return gpt4_custom_chatbot

# https://ai.google.dev/tutorials/python_quickstart

import re
import asyncio

from loguru import logger
from google.ai import generativelanguage as glm
from google.api_core.exceptions import GoogleAPIError
from google.generativeai.types.generation_types import (
    StopCandidateException,
    BlockedPromptException,
)

from scripts import gvars, strings, util, prompts
from scripts.types import ModelOutput


async def process_message_gemini(
    chatdata,  # ChatData
    model_args: dict,
    model_input: dict,
) -> ModelOutput:
    access_check = util.access_scope_filter(gvars.scope_gemini, chatdata.chat_id)
    if not access_check:
        return ModelOutput(
            text=f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )

    if not chatdata.gemini_session:
        try:
            preset = model_args.get("preset")
            new_chat = gvars.gemini_client.start_chat(history=[])

            match preset:
                case "default":
                    pass
                case "aris":
                    new_chat.history = [
                        glm.Content(
                            parts=[glm.Part(text=prompts.aris_prompt_gemini)],
                            role="user",
                        ),
                        glm.Content(
                            parts=[glm.Part(text=prompts.gemini_initial_response)],
                            role="model",
                        ),
                        glm.Content(
                            parts=[glm.Part(text=prompts.initial_prompts["input"])],
                            role="user",
                        ),
                        glm.Content(
                            parts=[glm.Part(text=prompts.initial_prompts["output"])],
                            role="model",
                        ),
                    ]
                case "custom":
                    custom_preset = chatdata.gemini_preset
                    try:
                        new_chat.history = [
                            glm.Content(
                                parts=[glm.Part(text=custom_preset["prompt"])],
                                role="user",
                            ),
                            glm.Content(
                                parts=[glm.Part(text=prompts.gemini_initial_response)],
                                role="model",
                            ),
                            glm.Content(
                                parts=[glm.Part(text=custom_preset["sample_input"])],
                                role="user",
                            ),
                            glm.Content(
                                parts=[glm.Part(text=custom_preset["sample_output"])],
                                role="model",
                            ),
                        ]
                    except (TypeError, AttributeError, LookupError):
                        return ModelOutput(
                            text=f"{strings.internal_error}\n\nError message: `{strings.custom_preset_outdated}`"
                        )
                case "addon":
                    preset_id = model_args.get("id")
                    addon_preset = gvars.gemini_addons.get(preset_id)
                    try:
                        new_chat.history = [
                            glm.Content(
                                parts=[glm.Part(text=addon_preset["prompt"])],
                                role="user",
                            ),
                            glm.Content(
                                parts=[glm.Part(text=prompts.gemini_initial_response)],
                                role="model",
                            ),
                        ]

                        if addon_preset.get("sample_io"):
                            for io_pair in addon_preset.get("sample_io"):
                                new_chat.history.append(
                                    glm.Content(
                                        parts=[glm.Part(text=io_pair["input"])],
                                        role="user",
                                    )
                                )
                                new_chat.history.append(
                                    glm.Content(
                                        parts=[glm.Part(text=io_pair["output"])],
                                        role="model",
                                    )
                                )
                    except (TypeError, AttributeError, LookupError) as e:
                        logger.error(
                            f"Error happened when loading gemini addon: {e}\nPreset id:{preset_id}"
                        )
                        return ModelOutput(
                            text=f"{strings.internal_error}\n\nError message: `{strings.addon_preset_invalid}\n{preset_id}: {e}`\n\n{strings.feedback}"
                        )
                case _:
                    return ModelOutput(
                        text=f"{strings.internal_error}\n\nError message: `Invalid preset for gemini model: {preset}`"
                    )

            chatdata.gemini_session = new_chat
        except Exception as e:
            logger.error(
                f"Error happened when creating gemini chat session in chat {chatdata.chat_id}: {e}"
            )
            return ModelOutput(
                text=f"{strings.api_error}\n\nError Message:\n`{strings.gemini_chatbot_creation_failed}: {e}`"
            )
    elif "gemini" in chatdata.concurrent_lock:
        return ModelOutput(text=strings.concurrent_locked)
    elif chatdata.gemini_clear_task is not None:
        chatdata.gemini_clear_task.cancel()
        chatdata.gemini_clear_task = None

    input_text = model_input.get("text")
    if model_args.get("preset") != "aris" and input_text.startswith("爱丽丝"):
        if model_args.get("preset") == "addon" and gvars.gemini_addons.get(
            model_args.get("id")
        ).get("ai_prefix"):
            input_text = input_text.replace(
                "爱丽丝", gvars.gemini_addons.get(model_args.get("id")).get("ai_prefix"), 1
            )
        else:
            input_text = re.sub(r"^爱丽丝[，。！？；：,.!?;:]*\s*", "", input_text)
    input_text = input_text or "Hi"  # Gemini does not accept empty string

    chatdata.concurrent_lock.add("gemini")
    try:
        response = await chatdata.gemini_session.send_message_async(input_text)
    # Exception str: stop/block_reason: OTHER
    except (StopCandidateException, BlockedPromptException):
        return ModelOutput(
            text=f"{strings.gemini_stop_error}\n\nError Message:\n`{strings.gemini_stopped_with_other_reason}`"
        )
    except GoogleAPIError as e:
        return ModelOutput(
            text=f"{strings.google_api_error}\n\nError Message:\n`{e}`"
        )
    except Exception as e:
        logger.error(
            f"Error happened when calling gemini_chatbot.send_message_async in chat {chatdata.chat_id}: {e}"
        )
        return ModelOutput(
            text=f"{strings.api_error}\n\nError Message:\n`{e}`\n\n{strings.try_reset}"
        )
    finally:
        chatdata.concurrent_lock.discard("gemini")

    output_text = response.text.strip()

    if chatdata.is_group and gvars.gemini_chatbot_close_delay > 0:

        async def scheduled_auto_close():
            await asyncio.sleep(gvars.gemini_chatbot_close_delay)
            chatdata.gemini_session = None

        chatdata.gemini_clear_task = asyncio.create_task(scheduled_auto_close())

    return ModelOutput(text=output_text)

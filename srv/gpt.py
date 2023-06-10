import logging
import prompts
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from scripts import gvars, strings, util


async def process_message_gpt35(
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

    aris_prompt = PromptTemplate(
        input_variables=["history", "input"], template=prompts.aris_prompt_template
    )
    conversation_model = ChatOpenAI(
        model="gpt-3.5-turbo", temperature=1, openai_api_key=api_key
    )

    if not chatdata.gpt35_history:
        chatdata.gpt35_history = ConversationSummaryBufferMemory(
            human_prefix="老师",
            ai_prefix="爱丽丝",
            llm=ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=api_key),
            max_token_limit=1024,
        )

    if not chatdata.gpt35_conversation:
        chatdata.gpt35_conversation = ConversationChain(
            llm=conversation_model, prompt=aris_prompt, memory=chatdata.gpt35_history
        )
    from langchain.callbacks import get_openai_callback

    with get_openai_callback() as cb:
        response = await chatdata.gpt35_conversation.apredict(
            input=model_input.get("text")
        )
        logging.info(f"Total Tokens: {cb.total_tokens}")
        logging.info(f"Prompt Tokens: {cb.prompt_tokens}")
        logging.info(f"Completion Tokens: {cb.completion_tokens}")
        logging.info(f"Total Cost (USD): ${cb.total_cost}")

    return {"text": response}


# import os
# import re
# import logging
# import openai
# import prompts
# import asyncio
# from collections import deque

# default_api_key = os.getenv("OPENAI_API_KEY")
# max_history = int(os.getenv("MAX_HISTORY", 10))
# max_input_length = int(os.getenv("MAX_INPUT_LENGTH", 100))
# max_output_length = int(os.getenv("MAX_OUTPUT_LENGTH", 500))
# flood_control_delay = int(os.getenv("FLOOD_CONTROL_DELAY"))


# async def process_message_gpt(event, **kwargs):
#     retry = kwargs.get("retry")
#     history = kwargs.get("history")
#     userlist = kwargs.get("userlist")
#     whitelist = kwargs.get("whitelist")
#     add_reply = kwargs.get("add_reply")
#     db_apikey = kwargs.get("db_apikey")
#     auto_clear = kwargs.get("auto_clear")
#     backup_key = kwargs.get("backup_key")
#     flood_ctrl = kwargs.get("flood_ctrl")

#     # Reset clearing chat history counter
#     if auto_clear:
#         auto_clear.pop(event.chat_id, auto_clear)

#     using_prompt = prompts.system_prompt
#     if retry:
#         using_prompt = prompts.backup_prompt

#     messages = [
#         {
#             "role": "system",
#             "content": using_prompt,
#         },
#     ]

#     # Avoid appending unwanted text into history
#     no_record = False
#     no_record_reason = None

#     if event.chat_id not in history:
#         history[event.chat_id] = deque(prompts.initial_prompts, maxlen=max_history)

#     # Process replied message
#     if not retry and add_reply:
#         history[event.chat_id].append(add_reply)
#         if len(add_reply.get("content")) > max_input_length:
#             no_record = True
#             no_record_reason = prompts.no_record_reason.get("reply_too_long")

#     # Process user input
#     if not retry:
#         input_text = re.sub(r"^/\S*", "", event.raw_text).strip()
#         history[event.chat_id].append(
#             {
#                 "role": "user",
#                 "content": input_text,
#             }
#         )
#         if len(input_text) > max_input_length:
#             no_record = True
#             no_record_reason = prompts.no_record_reason.get("input_too_long")

#     messages = messages + [i for i in history[event.chat_id]]

#     # Send API request
#     try:
#         api_key = (
#             backup_key
#             or db_apikey.get(event.chat_id)
#             or event.chat_id in whitelist
#             and default_api_key
#             or event.sender_id
#             and db_apikey.get(event.sender_id)
#             or None
#         )
#         response = await openai.ChatCompletion.acreate(
#             api_key=api_key,
#             model="gpt-3.5-turbo",
#             messages=messages,
#         )
#     except openai.error.AuthenticationError as e:
#         apikey_owner = backup_key and event.sender_id or event.chat_id
#         db_apikey.delete(apikey_owner)
#         userlist.remove(apikey_owner)
#         return f"{prompts.api_error}\n\n({e})"
#     except openai.error.OpenAIError as e:
#         logging.error(f"OpenAI Error: {e}")
#         return f"{prompts.api_error}\n\n({e})"

#     output_text = response["choices"][0]["message"]["content"]

#     # Flood control
#     if flood_ctrl and event.sender_id is not None:
#         try:
#             token_used = response["usage"]["completion_tokens"]
#             if event.sender_id not in flood_ctrl[event.chat_id]:
#                 flood_ctrl[event.chat_id][event.sender_id] = 0
#             flood_ctrl[event.chat_id][event.sender_id] += token_used

#             async def clear_flood_control_counter():
#                 await asyncio.sleep(flood_control_delay)
#                 try:
#                     flood_ctrl[event.chat_id][event.sender_id] = max(
#                         0, flood_ctrl[event.chat_id][event.sender_id] - token_used
#                     )
#                 except KeyError as e:
#                     logging.warning(
#                         f"KeyError: {e}, flood_ctrl might be deactivated during sleeping"
#                     )

#             asyncio.create_task(clear_flood_control_counter())
#         except KeyError as e:
#             logging.warning(
#                 f"KeyError: {e}, flood_ctrl might be deactivated during awaiting"
#             )

#     # Post-process
#     if len(output_text) > max_output_length:
#         no_record = True
#         no_record_reason = prompts.no_record_reason.get("output_too_long")
#     else:
#         for text_filter in prompts.text_filters:
#             if text_filter in output_text:
#                 if not retry:
#                     return await process_message_gpt(
#                         event,
#                         retry=True,
#                         history=history,
#                         userlist=userlist,
#                         whitelist=whitelist,
#                         add_reply=add_reply,
#                         db_apikey=db_apikey,
#                         auto_clear=auto_clear,
#                         backup_key=backup_key,
#                         flood_ctrl=flood_ctrl,
#                     )
#                 else:
#                     no_record = True
#                     no_record_reason = prompts.no_record_reason.get("filtered")
#                     break

#     # Output
#     try:
#         if no_record:
#             history[event.chat_id].pop()
#             if add_reply:
#                 history[event.chat_id].pop()

#             output_text = prompts.no_record.format(output_text, no_record_reason)
#         else:
#             history[event.chat_id].append(
#                 {
#                     "role": "assistant",
#                     "content": output_text,
#                 }
#             )

#             if retry:
#                 output_text = prompts.profanity_warn.format(output_text)

#         if backup_key:
#             output_text = prompts.backup_key_used.format(output_text)
#     except KeyError as e:
#         logging.warning(f"KeyError: {e}, history might be cleared during awaiting")

#     return output_text

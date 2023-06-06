import re
import openai
from scripts import strings
from scripts.util import load_chat, is_group, get_raw_text
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Welcome/help message
async def help_handler(message):
    try:
        sender = message.from_user
        name = f"{sender.first_name and sender.first_name or ''} {sender.last_name and sender.last_name or ''}".strip()
    except AttributeError:
        name = ""
    await message.reply(strings.manual.format(name))


# Version info and update log
async def version_handler(message):
    await message.reply(strings.version)


# Get current chat id
async def chatid_handler(message):
    await message.reply(f"Chat ID: `{message.chat.id}`")


# Model selection
async def model_selection_handler(message):
    await message.reply(
        strings.choose_model,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        strings.models.get("model-gpt35"), callback_data="model-gpt35"
                    )
                ],
                [
                    InlineKeyboardButton(
                        strings.models.get("model-bing"), callback_data="model-bing"
                    )
                ],
                [
                    InlineKeyboardButton(
                        strings.models.get("model-bard"), callback_data="model-bard"
                    )
                ],
            ]
        ),
    )


# Model selection callback
async def model_selection_callback_handler(query):
    modelname = query.data.decode().replace("model-", "")
    if modelname == "gpt35":
        chatdata = load_chat(query.message.chat.id)
        if chatdata and chatdata.openai_api_key:
            await query.message.edit(
                strings.model_choose_preset,
                reply_markup=InlineKeyboardMarkup(
                    [
                        InlineKeyboardButton(
                            strings.gpt35_presets.get("aris"),
                            callback_data="gpt35preset-aris",
                        ),
                        InlineKeyboardButton(
                            strings.gpt35_presets.get("default"),
                            callback_data="gpt35preset-default",
                        ),
                    ]
                ),
            )
        else:
            await query.message.edit(strings.no_auth)
    elif modelname == "bing":
        await query.message.edit(
            strings.bing_choose_style,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        "creative",
                        callback_data="bingstyle-creative",
                    ),
                    InlineKeyboardButton(
                        "balanced",
                        callback_data="bingstyle-balanced",
                    ),
                    InlineKeyboardButton(
                        "precise",
                        callback_data="bingstyle-precise",
                    ),
                ]
            ),
        )
    elif modelname == "bard":
        await query.message.edit(
            strings.model_choose_preset,
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        strings.bard_presets.get("default"),
                        callback_data="bardpreset-default",
                    ),
                    InlineKeyboardButton(
                        strings.bard_presets.get("cn"),
                        callback_data="bardpreset-cn",
                    ),
                ]
            ),
        )


# GPT-3.5 preset selection callback
async def gpt35_preset_selection_callback_handler(query):
    preset = query.data.decode().replace("gpt35preset-", "")
    chatdata = load_chat(query.message.chat.id)
    chatdata.set_model(
        {
            "name": "gpt35",
            "args": {"preset": preset},
        }
    )

    await query.message.edit(
        strings.model_changed
        + strings.models.get("model-gpt35")
        + f" ({strings.gpt35_presets.get(preset).split(' ')[0]})"
    )


# Bing style selection callback
async def bing_style_selection_callback_handler(query):
    style = query.data.decode().replace("bingstyle-", "")
    chatdata = load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await is_group(query.message.chat),
    )
    chatdata.set_model({"name": "bing", "args": {"style": style}})

    await query.message.edit(
        strings.model_changed + strings.models.get("model-bing") + f" ({style})"
    )


# Bard preset selection callback
async def bard_preset_selection_callback_handler(query):
    preset = query.data.decode().replace("bardpreset-", "")
    chatdata = load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await is_group(query.message.chat),
    )
    chatdata.set_model({"name": "bard", "args": {"preset": preset}})

    await query.message.edit(
        strings.model_changed
        + strings.models.get("model-bard")
        + f" ({strings.bard_presets.get(preset).split(' ')[0]})"
    )


# Set OpenAI API key
async def api_key_handler(message):
    api_key_input = re.sub(r"^/\S*\s*", "", message.text)
    if api_key_input.startswith("sk-"):
        try:
            await openai.ChatCompletion.acreate(
                api_key=api_key_input,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Test message, please reply '1'"}
                ],
            )

            chatdata = load_chat(
                message.chat.id, create_new=True, is_group=await is_group(message.chat)
            )
            chatdata.set_api_key(api_key_input)
            await message.reply(strings.api_key_set)
        except openai.error.OpenAIError as e:
            await message.reply(
                f"{strings.api_key_invalid}\n\nError message:`{e}`\n\n{strings.api_key_common_errors}"
            )
    else:
        await message.reply(strings.api_key_invalid)


# Conversation
async def conversation_handler(message):
    chatdata = load_chat(message.chat.id)
    if not chatdata:
        await message.reply(strings.no_auth)
    else:
        raw_text = await get_raw_text(message)
        input_text = re.sub(r"^/\S*\s*", "", raw_text)

        if message.reply_to_message:
            context = await get_raw_text(message.reply_to_message)
            input_text = f'Context: "{context}";\n{input_text}'

        model_output = await chatdata.process_message(input_text)
        await message.reply(model_output.get("text", "`No output text available`"))


# Manage mode
async def manage_mode_handler(message):
    message.reply("under development")

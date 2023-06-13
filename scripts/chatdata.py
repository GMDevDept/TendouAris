import json
import asyncio
from pyrogram import Client
from typing import Optional
from asyncio import Task
from EdgeGPT import Chatbot as BingChatbot
from Bard import AsyncChatbot as BardChatbot
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from scripts import gvars, strings
from srv.gpt import process_message_gpt35, process_message_gpt4
from srv.bing import process_message_bing
from srv.bard import process_message_bard


class ChatData:
    total_chats = 0

    def __init__(
        self,
        chat_id: int,
        model: dict = {"name": "gpt35", "args": {"preset": "aris"}},
        **kwargs,
    ):
        self.chat_id: int = chat_id
        self.is_group: Optional[bool] = None
        self.model: dict = model  # {"name": str, "args": dict}
        self.openai_api_key: Optional[str] = kwargs.get("openai_api_key")
        self.gpt35_preset: Optional[dict] = kwargs.get("gpt35_preset")
        self.gpt35_chatbot: Optional[ConversationChain] = None
        self.gpt35_history: Optional[ConversationSummaryBufferMemory] = None
        self.gpt35_clear_task: Optional[Task] = None
        self.gpt4_preset: Optional[dict] = kwargs.get("gpt4_preset")
        self.gpt4_chatbot: Optional[ConversationChain] = None
        self.gpt4_history: Optional[ConversationSummaryBufferMemory] = None
        self.gpt4_clear_task: Optional[Task] = None
        self.bing_chatbot: Optional[BingChatbot] = None
        self.bing_blocked: Optional[bool] = None
        self.bing_clear_task: Optional[Task] = None
        self.bard_chatbot: Optional[BardChatbot] = None
        self.bard_blocked: Optional[bool] = None
        self.bard_clear_task: Optional[Task] = None
        self.last_reply: Optional[str] = None

        ChatData.total_chats += 1

    @property
    def persistent_data(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "is_group": self.is_group,
            "model": self.model,
            "openai_api_key": self.openai_api_key,
            "gpt35_preset": self.gpt35_preset,
            "gpt4_preset": self.gpt4_preset,
        }

    def save(self):
        gvars.all_chats.update({self.chat_id: self})
        data_json = json.dumps(self.persistent_data)
        gvars.db_chatdata.set(self.chat_id, data_json)

    @classmethod
    def load(cls, data_json: str) -> "ChatData":
        data = json.loads(data_json)
        if data.get("is_group"):
            chatdata = GroupChatData(**data)
        else:
            chatdata = ChatData(**data)
        gvars.all_chats.update({data["chat_id"]: chatdata})
        return chatdata

    def set_model(self, model: dict):
        self.model = model
        self.save()

    def set_api_key(self, api_key: str):
        self.openai_api_key = api_key
        self.save()

    def set_gpt35_preset(self, preset: dict):
        self.gpt35_preset = preset
        self.save()

    def set_gpt4_preset(self, preset: dict):
        self.gpt4_preset = preset
        self.save()

    async def process_message(
        self, client: Client, model_input: dict
    ) -> Optional[dict]:
        model_name, model_args = self.model["name"], self.model["args"]
        model_output = None
        match model_name:
            case "gpt35":
                model_output = await process_message_gpt35(
                    client=client,
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "gpt4":
                model_output = await process_message_gpt4(
                    client=client,
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "bing":
                model_output = await process_message_bing(
                    client=client,
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "bard":
                model_output = await process_message_bard(
                    client=client,
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
        return model_output

    async def reset(self):
        if self.bing_chatbot:
            await self.bing_chatbot.close()
        self.gpt35_chatbot = None
        self.gpt35_history = None
        self.gpt35_clear_task = None
        self.gpt4_chatbot = None
        self.gpt4_history = None
        self.gpt4_clear_task = None
        self.bing_chatbot = None
        self.bing_blocked = None
        self.bing_clear_task = None
        self.bard_chatbot = None
        self.bard_blocked = None
        self.bard_clear_task = None
        self.last_reply = None


class GroupChatData(ChatData):
    total_chats = 0

    def __init__(self, chat_id: int, **kwargs):
        super().__init__(chat_id, **kwargs)
        self.is_group = True
        self.flood_control_enabled: Optional[bool] = (
            kwargs.get("flood_control_enabled") is not False  # default to be True
        )
        self.flood_control_record: Optional[dict] = None

        GroupChatData.total_chats += 1

    @property
    def persistent_data(self):
        data = super().persistent_data
        data.update(
            {
                "flood_control_enabled": self.flood_control_enabled,
            }
        )
        return data

    def set_flood_control(self, enable: bool):
        self.flood_control_enabled = enable
        self.save()

    async def process_message(
        self, client: Client, model_input: dict
    ) -> Optional[dict]:
        if not self.flood_control_enabled:
            return await super().process_message(client, model_input)
        else:
            if not self.flood_control_record:
                self.flood_control_record = {}

            sender_id = model_input.get("sender_id")
            if (
                sender_id in self.flood_control_record
                and self.flood_control_record[sender_id]["count"]
                >= gvars.flood_control_count
            ):
                return {"text": strings.flood_control_activated}

            model_output = await super().process_message(client, model_input)

            async def clear_flood_control_counter():
                await asyncio.sleep(gvars.flood_control_interval)
                if self.flood_control_record and sender_id in self.flood_control_record:
                    self.flood_control_record[sender_id]["count"] = 0
                    self.flood_control_record[sender_id]["clear_task"] = None

            if sender_id not in self.flood_control_record:
                self.flood_control_record[sender_id] = {
                    "count": 0,
                    "clear_task": None,
                }

            self.flood_control_record[sender_id]["count"] += 1
            if self.flood_control_record[sender_id]["clear_task"] is not None:
                self.flood_control_record[sender_id]["clear_task"].cancel()
            self.flood_control_record[sender_id]["clear_task"] = asyncio.create_task(
                clear_flood_control_counter()
            )

            return model_output

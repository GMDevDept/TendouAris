import json
from typing import Optional
from EdgeGPT import Chatbot as BingChatbot
from Bard import Chatbot as BardChatbot
from scripts import globals
from srv.gpt import process_message_gpt
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
        self.model: dict = model  # {"name": str, "args": dict}
        self.openai_api_key: Optional[str] = kwargs.get("openai_api_key")
        self.bing_chatbot: Optional[BingChatbot] = None
        self.bard_chatbot: Optional[BardChatbot] = None
        self.history = None

        ChatData.total_chats += 1

    @property
    def persistent_data(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "model": self.model,
            "openai_api_key": self.openai_api_key,
        }

    def save(self):
        globals.all_chats.update({self.chat_id: self})
        data_json = json.dumps(self.persistent_data)
        globals.db_chatdata.set(self.chat_id, data_json)

    @classmethod
    def load(cls, data_json: str) -> "ChatData":
        data = json.loads(data_json)
        chat_id = data["chat_id"]
        if data.get("is_group"):
            chatdata = GroupChatData(chat_id, **data)
        else:
            chatdata = ChatData(chat_id, **data)
        globals.all_chats.update({chat_id: chatdata})
        return chatdata

    def set_api_key(self, api_key: str):
        self.openai_api_key = api_key
        self.save()

    def set_model(self, model: dict):
        self.model = model
        self.save()

    async def process_message(self, input_text: str) -> Optional[dict]:
        model_name, model_args = self.model["name"], self.model["args"]
        model_input = {"input_text": input_text}
        model_output = None
        match model_name:
            case "gpt35":
                model_output = await process_message_gpt(
                    chatdata=self, model_args=model_args, model_input=model_input
                )
            case "bing":
                model_output = await process_message_bing(
                    chatdata=self, model_args=model_args, model_input=model_input
                )
            case "bard":
                model_output = await process_message_bard(
                    chatdata=self, model_args=model_args, model_input=model_input
                )
        return model_output


class GroupChatData(ChatData):
    total_chats = 0

    def __init__(self, chat_id: int, **kwargs):
        super().__init__(chat_id, **kwargs)
        self.is_group = True
        self.auto_clear_enable: Optional[bool] = kwargs.get("auto_clear_enable")
        self.floodctrl_enable: Optional[bool] = kwargs.get("floodctrl_enable")

        GroupChatData.total_chats += 1

    @property
    def persistent_data(self):
        data = super().persistent_data
        data.update(
            {
                "is_group": self.is_group,
                "auto_clear_enable": self.auto_clear_enable,
                "floodctrl_enable": self.floodctrl_enable,
            }
        )
        return data

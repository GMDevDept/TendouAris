from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from curl_cffi import requests
from loguru import logger

from .const import (
    OI_Headers,
    GAC_Headers,
    UL_Headers,
    DEL_Headers,
    CCH_Headers,
    CNC_Headers,
    RC_Headers,
    SM_Headers,
)
from .util import (
    parse_proxy_url,
    process_cookie,
    get_content_type,
    build_request,
    run_in_new_thread,
)
from ..util import retry, run_sync

loop = asyncio.new_event_loop()


class ClaudeAiClient:
    def __init__(self, cookie: str | Path | list[dict], proxy: str = None):
        self.cookie_str = process_cookie(cookie)
        self.proxy_dict = parse_proxy_url(proxy) if proxy else None
        self.organization_id = ""

    async def init(self):
        self.organization_id = await self.get_organization_id()
        return self

    def process_header(self, headers: dict):
        """给Headers加上cookie str"""
        return {**headers, **{"cookie": self.cookie_str}}

    @retry(3, "Failed to get organization id")
    @run_sync
    def get_organization_id(self):
        """获取 organization_id"""

        resp = requests.get(
            "https://claude.ai/api/organizations",
            headers=self.process_header(OI_Headers),
            proxies=self.proxy_dict,
            impersonate="chrome110",
        )
        data = resp.json()
        return data[0]["uuid"]

    @retry(3, "Failed to get chat history")
    @run_sync
    def get_chat_history(self, chat_id):
        """获取某个聊天窗口的所有对话消息"""

        resp = requests.get(
            f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations/{chat_id}",
            headers=self.process_header(CCH_Headers),
            proxies=self.proxy_dict,
            impersonate="chrome110",
        )
        return resp.json()

    @retry(3, "Failed to get all chats")
    @run_sync
    def get_all_chats(self):
        """获取所有的对话窗口"""

        resp = requests.get(
            f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations",
            headers=self.process_header(GAC_Headers),
            proxies=self.proxy_dict,
            impersonate="chrome110",
        )
        conversations = resp.json()

        if resp.status_code == 200:
            return conversations
        else:
            raise Exception(resp.text())

    @retry(3, "Failed to create new chat")
    @run_sync
    def create_new_chat(self):
        """创建新的对话窗口"""
        random_uuid = str(uuid.uuid4())
        resp = requests.post(
            f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations",
            headers=self.process_header(CNC_Headers),
            data=json.dumps({"uuid": random_uuid, "name": ""}),
            proxies=self.proxy_dict,
            impersonate="chrome110",
        )

        if resp.status_code == 201:
            return resp.json()
        else:
            raise Exception(f"code: {resp.status_code}, error: {resp.text()}")

    @retry(3, "Failed to delete chat")
    @run_sync
    def delete_chat(self, chat_id):
        """删除对话窗口"""

        resp = requests.delete(
            f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations/{chat_id}",
            headers=self.process_header(DEL_Headers),
            data=json.dumps(f"{chat_id}"),
            proxies=self.proxy_dict,
            impersonate="chrome110",
        )
        if resp.status_code != 204:
            raise Exception(f"code: {resp.status_code}, error: {resp.text()}")

    @retry(3, "Failed to rename chat")
    @run_sync
    def rename_chat(self, title, chat_id):
        """重命名对话窗口"""
        resp = requests.post(
            "https://claude.ai/api/rename_chat",
            headers=self.process_header(RC_Headers),
            json={
                "organization_uuid": self.organization_id,
                "conversation_uuid": chat_id,
                "title": title,
            },
            proxies=self.proxy_dict,
            impersonate="chrome110",
        )
        if not resp.status_code == 200:
            raise Exception(f"code: {resp.status}, error: {resp.text()}")

    async def ask_stream(
        self, question: str, chat_id: str = None, attachment: str | Path = None
    ):
        """发送消息并且异步生成器式的获取返回消息"""
        from ..util import retry

        bytes_queue = asyncio.Queue()

        @retry(3, "Failed to send message")
        def put_message():
            requests.post(
                "https://claude.ai/api/append_message",
                headers=self.process_header(SM_Headers),
                json=build_request(self, question, chat_id, attachment),
                proxies=self.proxy_dict,
                impersonate="chrome110",
                content_callback=bytes_queue.put_nowait,
            )

        run_in_new_thread(put_message)

        retry = 10
        finished = False
        while not finished:
            if retry <= 0:
                logger.warning("Faield to get answer from claude. Timed out.")
                break
            try:
                data = bytes_queue.get_nowait()
                if isinstance(data, bytes):
                    retry = 5
                    datas = [
                        json.loads(data.rstrip("\n\n"))
                        for data in data.decode("utf-8").split("data: ")
                        if data
                    ]
                    for data in datas:
                        if data["stop_reason"]:
                            finished = True
                            break
                        elif data["completion"]:
                            yield data["completion"]
                else:
                    raise Exception(f"Expect bytes, but received:{data}")
            except json.JSONDecodeError:
                data_str = data.decode("utf-8")
                if "error" in data_str:
                    raise Exception(f"Error occured: {data_str}")
                else:
                    logger.warning(f"Unkonwn JsonDecodeError:{data}")
            except Exception as e:
                retry -= 1
                await asyncio.sleep(2)

    @retry(3, "Failed to upload attachment")
    def upload_attachment(self, file_path: str | Path):
        """上传附件"""
        file_path = Path(file_path)

        if file_path.suffix == ".txt":
            file_name = file_path.name
            file_size = file_path.stat().st_size
            file_type = "text/plain"

            with file_path.open("r", encoding="utf-8") as f:
                file_content = f.read()

            return {
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "extracted_content": file_content,
            }

        resp = requests.post(
            "https://claude.ai/api/convert_document",
            headers=self.process_header(UL_Headers),
            json={
                "file": (
                    file_path.name,
                    open(file_path, "rb"),
                    get_content_type(file_path),
                ),
                "orgUuid": (None, self.organization_id),
            },
            proxies=self.proxy_dict,
            impersonate="chrome110",
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"code: {resp.status_code}, error: { resp.text()}")

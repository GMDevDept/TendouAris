from __future__ import annotations

import asyncio
import json
import ssl
import urllib.parse
import uuid
from json import JSONDecodeError
from pathlib import Path
from time import time
from typing import List, Literal, AsyncGenerator, Any

import aiohttp
import certifi
from loguru import logger
from regex import regex

from .const import HEADERS, WSSHEADERS, ConversationStyle, DELETE_HEADERS, DRAW_HEADERS
from .type import (
    Notice,
    Text,
    Response,
    Apology,
    SuggestRely,
    SourceAttribution,
    SearchResult,
    Image,
    Limit,
    NewChat,
)
from .utils import (
    process_cookie,
    append_identifier,
    build_chat_request,
    guess_locale,
    async_retry,
    parse_proxy_url,
)  # noqa: E501

ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(certifi.where())


class Bing_Client:
    def __init__(
        self, cookie: str | Path | List[dict], proxy=None, wss_link: str = None
    ):
        self.chats: dict = {}
        self.client_id: str = ""
        self.sent_times: int = 0
        self.cookie_jar = process_cookie(cookie)
        self.proxy = parse_proxy_url(proxy) if proxy else None
        self.wss_link = wss_link

    @property
    def chat_list(self):
        return [{key: value} for key, value in self.chats.items()]

    async def init(self):
        """初始化bing client"""
        logger.info("creating Bing Client - - -.")
        await self.get_chats()
        await self.load_all_chats(load_history=False)
        logger.info("Succeed to creat Bing Client.")
        return self

    @async_retry(10)
    async def create_chat(self):
        """创建一个新的对话,返回一个包含新对话信息的dict,可以直接传入到ask_stream中进行使用"""
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                "https://www.bing.com/turing/conversation/create",
                headers=HEADERS,
                proxy=self.proxy,
            ) as response:
                try:
                    data = await response.json()
                    access_token = response.headers.get(
                        "X-Sydney-EncryptedConversationSignature"
                    )
                    if access_token:
                        data["access_token"] = urllib.parse.quote(access_token, safe="")
                    new_chat = {data["conversationId"]: {**data, "time": time()}}
                    logger.info("Succeed to creat new chat")
                    self.chats = {**new_chat, **self.chats}
                    return new_chat
                except Exception:
                    error = await response.text()
                    raise Exception(error)

    async def draw(self, prompt: str) -> List[Image] | Apology:
        """按照传入的prompt进行绘图,这个功能可以直接在ask_stream中被自动调用并返回图片或bing的apology"""
        url_encoded_prompt = urllib.parse.quote(f"prompt='{prompt}'")

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(
            cookie_jar=self.cookie_jar,
            headers=DRAW_HEADERS,
            timeout=timeout,
        ) as session:
            response = await session.get(
                url=f"https://www.bing.com/images/create?partner=sydney&re=1&showselective=1&sude=1&kseed=8000&SFX=3&q={url_encoded_prompt}&iframeid={uuid.uuid4()}",
                allow_redirects=False,
                proxy=self.proxy,
            )
            if response.status != 302:
                return Apology(content="Drawing Failed: Redirect failed")
            resp_text = await response.text()
            if "this prompt has been blocked" in resp_text.lower():
                return Apology(
                    content="Your prompt has been blocked by Bing. Try to change any bad words and try again."
                )
            redirect_url = f"https://www.bing.com{response.headers['Location']}"
            response = await session.get(
                redirect_url,
                allow_redirects=False,
                proxy=self.proxy,
            )
            resp_text = await response.text()
            if "blocked" in resp_text:
                return Apology(
                    content="Your prompt has been blocked by Bing. Try to change any bad words and try again."
                )
            if response.status != 302:
                response = await session.get(
                    redirect_url.replace("rt=4", "rt=3"),
                    allow_redirects=False,
                    proxy=self.proxy,
                )
                resp_text = await response.text()
                if "blocked" in resp_text:
                    return Apology(
                        content="Your prompt has been blocked by Bing. Try to change any bad words and try again."
                    )
                if response.status != 302:
                    return Apology(content="Drawing Failed: Redirect failed")

            request_id = response.headers["Location"].split("id=")[-1]

            polling_url = f"https://www.bing.com/images/create/async/results/{request_id}?q={url_encoded_prompt}"

            while True:
                response = await session.get(polling_url, proxy=self.proxy)
                if response.status != 200:
                    return Apology(content="Drawing Failed: Could not get results")
                content = await response.text()

                if content:
                    break
                else:
                    await asyncio.sleep(1)

            image_links = regex.findall(r'src="([^"]+)"', content)

            normal_image_links = [link.split("?w=")[0] for link in image_links]

            normal_image_links = list(set(normal_image_links))
            normal_image_links = [
                link for link in normal_image_links if "r.bing.com" not in link
            ]
            if not normal_image_links:
                return Apology(content="Drawing Failed: No images are found.")
            result_images = []
            for index, image in enumerate(normal_image_links):
                result_images.append(Image(name=f"img{index + 1}.png", url=image))
            return result_images

    async def ask_stream(
        self,
        question: str,
        image: str | Path | bytes = None,
        chat: dict = None,
        conversation_style: ConversationStyle
        | Literal["creative", "balanced", "precise"] = ConversationStyle.Creative,
        personality=None,
        yield_search: bool = False,
        locale=guess_locale(),
    ):
        """返回纯文本信息的 ask_stream,其中的链接和图片链接均处理成了markdown格式,是对ask_stream_raw的封装"""
        sources = []
        suggest_reply = []
        images = []
        limit = None
        async for data in self.ask_stream_raw(
            question, image, chat, conversation_style, personality, locale=locale
        ):
            if isinstance(data, Text):
                yield data.content
            elif isinstance(data, SuggestRely):
                suggest_reply.append(data)
            elif isinstance(data, SourceAttribution):
                sources.append(data)
            elif isinstance(data, Apology):
                yield "\n" + data.content
            elif isinstance(data, Image):
                images.append(data)
            elif isinstance(data, Limit):
                limit = data
            elif isinstance(data, SearchResult) and yield_search:
                yield str(data)
        for index, source in enumerate(sources):
            if index == 0:
                yield "\nSee more:  \n"
            yield f"({index + 1}):{source}  \n"
        for index, image in enumerate(images):
            if index == 0:
                yield "\nDrew images:  \n"
            yield f"{index + 1}:{image}  \n"
        for index, reply in enumerate(suggest_reply):
            if index == 0:
                yield "\nSuggest Replys:  \n"
            yield f"{index + 1}:{reply.content}  \n"
        if limit:
            yield f"\n\nLimit:{limit.num_user_messages} of {limit.max_num_user_messages}  "

    def get_chatdata(self, chat: dict):
        conversation_id = list(chat.keys())[0]

        if conversation_id in self.chats:
            chat_data = list(chat.values())[0]
            chat_data.update(self.chats[conversation_id])
        else:
            chat_data = list(chat.values())[0]
        return chat_data

    async def ask_stream_raw(
        self,
        question: str,
        image: str | Path | bytes = None,
        chat: dict = None,
        conversation_style: ConversationStyle = ConversationStyle.Creative,
        personality=None,
        locale=guess_locale(),
    ) -> AsyncGenerator[
        NewChat
        | Apology
        | Notice
        | SearchResult
        | Text
        | SourceAttribution
        | SuggestRely
        | Limit
        | Response
        | Any
    ]:
        """返回原始数据类型的流式对话生成器,返回的类型请在type中自行查看"""
        if not chat:
            chat = await self.create_chat()
            yield NewChat(chat=chat)

        chat_data = self.get_chatdata(chat)

        access_token = chat_data.get("access_token", "")
        conversation_signature = chat_data.get("conversationSignature", "")
        if access_token or (not conversation_signature):
            if (not chat_data.get("time") or time() - chat_data.get("time") > 2500) or (
                not conversation_signature
            ):
                await self.get_token(chat_data["conversationId"])
                self.chats[chat_data["conversationId"]]["time"] = time()
                chat_data = self.get_chatdata(chat)

            url = (
                (self.wss_link or "wss://sydney.bing.com/sydney/ChatHub")
                + "?sec_access_token="
                + chat_data.get("access_token", "")
            )

        else:
            url = self.wss_link or "wss://sydney.bing.com/sydney/ChatHub"
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            wss_headers = WSSHEADERS
            if self.cookie_jar is not None:
                wss_cookies = [
                    f"{cookie.key}={cookie.value}" for cookie in self.cookie_jar
                ]
                wss_headers["cookie"] = ";".join(wss_cookies)
            async with session.ws_connect(
                url=url, ssl=ssl_context, headers=wss_headers, proxy=self.proxy
            ) as wss:
                await wss.send_str(
                    append_identifier({"protocol": "json", "version": 1})
                )
                await wss.receive_str()
                await wss.send_str(append_identifier({"type": 6}))
                data = await build_chat_request(
                    self,
                    question,
                    chat_data,
                    conversation_style,
                    image,
                    personality,
                    locale,
                )
                await wss.send_str(append_identifier(data))
                last_text = ""
                apology = ""
                retry_count = 5
                sas = []
                image_tasks = []
                store_data = []
                while not wss.closed:
                    msg = await wss.receive(timeout=900)
                    if image_tasks:
                        for task in image_tasks:
                            if task.done():
                                image_tasks.remove(task)
                                result = task.result()
                                if isinstance(result, Apology):
                                    yield result
                                elif isinstance(result, list):
                                    for image in result:
                                        yield image

                    # 心跳
                    if int(time()) % 6 == 0:
                        await wss.send_str(append_identifier({"type": 6}))

                    # 设置错误上限次数
                    if not msg.data:
                        retry_count -= 1
                        if retry_count == 0:
                            raise Exception("No response from server")
                        continue

                    # 过滤 text 类响应
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        objects = msg.data.split("\x1e")
                    else:
                        continue

                    # 可能一个里面用 "\x1e" 分割出多个响应,也可能一个都没有
                    for obj in objects:
                        # 没有就跳过本次处理
                        if not obj:
                            continue

                        # 加载成json格式
                        response = json.loads(obj)
                        store_data.append(response)
                        with open("data1.json", "w") as f:
                            f.write(json.dumps(store_data))
                        # 用type来区分response的类型,并且只要bot发的消息,过滤掉
                        if (
                            response.get("type") == 1
                            and response["arguments"][0].get("messages")
                            and response["arguments"][0]["messages"]
                            and response["arguments"][0]["messages"][0].get(
                                "author", ""
                            )
                            == "bot"
                        ):  # noqa: E501
                            messages = response["arguments"][0]["messages"]
                            for message in messages:
                                if (
                                    message.get(
                                        "messageType",
                                    )
                                    == "GenerateContentQuery"
                                ):
                                    """Draw images"""
                                    image_tasks.append(
                                        asyncio.create_task(
                                            self.draw(message.get("text", ""))
                                        )
                                    )
                                if (
                                    message.get("messageType")
                                    == "InternalLoaderMessage"
                                ):  # noqa: E501
                                    yield Notice(content=message.get("text", ""))
                                elif (
                                    message.get("messageType") == "InternalSearchResult"
                                ):
                                    try:
                                        content = (
                                            json.loads(
                                                message.get(
                                                    "text",
                                                    message.get("hiddenText", "")
                                                    .replace("```json", "")
                                                    .replace("\n```", ""),
                                                )
                                            )
                                        ).get("web_search_results", [])
                                    except JSONDecodeError:
                                        content = message.get("text", "")
                                    yield SearchResult(content=content)
                                elif message["contentOrigin"] == "Apology":
                                    yield_text = message.get("text", "")[len(apology) :]
                                    apology = message.get("text", "")
                                    if yield_text:
                                        yield Apology(content=yield_text)

                                elif "messageType" not in message.keys():
                                    plain_text: str = message.get("text", "")
                                    if plain_text.endswith(
                                        (
                                            "[",
                                            "]",
                                            "(",
                                            ")",
                                            "^",
                                            "1",
                                            "2",
                                            "3",
                                            "4",
                                            "5",
                                            "6",
                                            "7",
                                            "8",
                                            "9",
                                            "0",
                                        )
                                    ):
                                        continue
                                    plain_text: str = (
                                        plain_text.replace("[^", "[")
                                        .replace("^]", "]")
                                        .replace("(^", "(")
                                        .replace("^)", ")")
                                    )
                                    yield_text = plain_text[len(last_text) :]
                                    last_text = plain_text

                                    if yield_text:
                                        yield Text(content=yield_text)

                                    if (
                                        message.get("sourceAttributions")
                                        and message["sourceAttributions"]
                                    ):
                                        for sa in message.get("sourceAttributions", ""):
                                            new_sa = SourceAttribution(
                                                display_name=sa.get(
                                                    "providerDisplayName",
                                                    sa.get("seeMoreUrl", ""),
                                                ),
                                                see_more_url=sa.get("seeMoreUrl", ""),
                                                image=Image(
                                                    url=sa.get("imageLink", ""),
                                                    base64=sa.get("imageFavicon", ""),
                                                ),
                                            )
                                            if new_sa not in sas:
                                                sas.append(new_sa)
                                                yield new_sa

                                    if (
                                        message.get("suggestedResponses")
                                        and message["suggestedResponses"]
                                    ):
                                        for suggest_dict in message.get(
                                            "suggestedResponses"
                                        ):
                                            suggest = suggest_dict.get("text", "")
                                            if suggest:
                                                yield SuggestRely(content=suggest)

                                    else:
                                        continue

                                else:
                                    continue
                        elif response.get("type") == 1 and (
                            (response.get("arguments", [{}]))[0]
                        ).get(
                            "throttling", ""
                        ):  # noqa: E501
                            limit = ((response.get("arguments", [{}]))[0]).get(
                                "throttling", ""
                            )
                            yield Limit(
                                max_num_user_messages=limit[
                                    "maxNumUserMessagesInConversation"
                                ],
                                num_user_messages=limit[
                                    "numUserMessagesInConversation"
                                ],
                                max_num_long_doc_summary_user_messages=limit[
                                    "maxNumLongDocSummaryUserMessagesInConversation"
                                ],
                                num_long_doc_summary_user_messages=limit[
                                    "numLongDocSummaryUserMessagesInConversation"
                                ],
                            )
                            if (
                                limit["maxNumUserMessagesInConversation"]
                                < limit["numUserMessagesInConversation"]
                            ):
                                yield Apology(
                                    content="The number of chats has reached the maximum, please open a new conversation\n聊天次数达到上限,请开启新的对话"
                                )
                                await wss.close()
                                continue
                        elif response.get("type") == 2:
                            if response["item"]["result"].get("error"):
                                await wss.close()
                                raise Exception(
                                    f"{response['item']['result']['value']}: {response['item']['result']['message']}",
                                )
                            await wss.close()
                            try:
                                if chat_data["conversationId"] not in self.chats.keys():
                                    self.chats[chat_data["conversationId"]] = {}
                                if (
                                    "message"
                                    not in self.chats[
                                        chat_data["conversationId"]
                                    ].keys()
                                ):
                                    self.chats[chat_data["conversationId"]][
                                        "message"
                                    ] = response["item"]["messages"]
                                else:
                                    self.chats[chat_data["conversationId"]][
                                        "message"
                                    ].append(response["item"]["messages"])
                            except Exception as e:
                                logger.error(
                                    f"Failed to add new messages to cache: {e}"
                                )  # noqa: E501

                            yield Response(content=response)
                            break
                    if response.get("type") != 2:
                        if response.get("type") == 6:
                            await wss.send_str(append_identifier({"type": 6}))
                        elif response.get("type") == 7:
                            await wss.send_str(append_identifier({"type": 7}))

                if image_tasks:
                    results = await asyncio.gather(*image_tasks)
                    for result in results:
                        if isinstance(result, Apology):
                            yield result
                        elif isinstance(result, list):
                            for image in result:
                                yield image
                        else:
                            yield Apology(content="Unknown error when drawing.")

    @async_retry(5)
    async def get_chats(self):
        """获取最多200个bing的会话窗口的信息"""
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                "https://www.bing.com/turing/conversation/chats",
                headers=HEADERS,
                proxy=self.proxy,
            ) as response:
                resp = await response.json()
                self.client_id = resp["clientId"]
                self.chats = {
                    chat["conversationId"]: {**chat, **{"isStart": False}}
                    for chat in resp["chats"]
                }
                logger.info("Succeed to get chat lists")
                return self.chats

    @async_retry(10)
    async def get_token(self, conversation_id):
        """获取对应聊天窗口的access_token"""
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(
            cookie_jar=self.cookie_jar, timeout=timeout
        ) as session:
            async with session.get(
                f"https://www.bing.com/turing/conversation/create?conversationId={urllib.parse.quote(conversation_id, safe='')}",
                headers=HEADERS,
                proxy=self.proxy,
            ) as response:
                access_token = response.headers.get(
                    "X-Sydney-EncryptedConversationSignature"
                )
                if access_token:
                    self.chats[conversation_id]["access_token"] = urllib.parse.quote(
                        access_token, safe=""
                    )  # noqa: E501
                else:
                    return

    @async_retry(10)
    async def get_chat_history(self, conversation_id):
        """获取对应的聊天窗口的所有消息"""
        conversation_signature = self.chats[conversation_id].get(
            "conversationSignature", None
        )
        if conversation_signature:
            url = f"https://sydney.bing.com/sydney/GetConversation?conversationId={conversation_id}&source=cib&participantId={self.client_id}&conversationSignature={urllib.parse.quote(conversation_signature)}&traceId={uuid.uuid4()}"
        else:
            url = f"https://sydney.bing.com/sydney/GetConversation?conversationId={conversation_id}&source=cib&participantId={self.client_id}&traceId={uuid.uuid4()}"
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(
            cookie_jar=self.cookie_jar, timeout=timeout
        ) as session:
            async with session.get(
                url,
                headers=HEADERS,
                proxy=self.proxy,
            ) as response:
                data = await response.json()
                self.chats[conversation_id]["message"] = data.get("messages", [])
                return

    async def load_chat_data(self, conversation_id, load_history: bool = False) -> None:
        """获取某个会话窗口的所有聊天信息(如果load_history)和access_token(如果有)"""
        tasks = [asyncio.create_task(self.get_token(conversation_id))]  # noqa: E501
        if load_history:
            tasks.append(asyncio.create_task(self.get_chat_history(conversation_id)))

        await asyncio.gather(*tasks)

    async def load_all_chats(self, load_history: bool = False):
        """并发拉取所有的chat的信息,并入client的chats进行缓存"""
        tasks = []
        for conversation_id in list(self.chats.keys()):
            task = asyncio.create_task(
                self.load_chat_data(conversation_id, load_history=load_history)
            )
            tasks.append(task)
        await asyncio.gather(*tasks)
        logger.info(
            f"Succeed to load all chat's data{'and history' if load_history else ''}"
        )
        return

    @async_retry(3)
    async def delete_conversation(self, conversation_id) -> None:
        """删除指定的会话"""
        if conversation_id not in self.chats.keys():
            await self.get_chats()
            await self.load_all_chats()
        if conversation_id not in self.chats.keys():
            raise Exception("The conversation didn't exist")
        else:
            async with aiohttp.ClientSession(
                cookie_jar=self.cookie_jar, headers=DELETE_HEADERS
            ) as session:
                async with session.post(
                    "https://sydney.bing.com/sydney/DeleteSingleConversation",
                    data=json.dumps(
                        {
                            "conversationId": conversation_id,
                            "conversationSignature": self.chats[conversation_id][
                                "conversationSignature"
                            ],
                            "participant": {"id": self.client_id},
                            "source": "cib",
                            "optionsSets": ["autosave"],
                        }
                    ),
                    proxy=self.proxy,
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Succeed to delete conservation:{conversation_id}")
                        del self.chats[conversation_id]
                        return
                    else:
                        text = await resp.text()
                        raise Exception(f"Failed to delete conversation:{text}")

    async def delete_conversation_by_count(
        self, count: int = 20, del_all: bool = False
    ):
        """按照数量删除你的对话窗口,也可以设置全部删除"""
        chats = list(self.chats.values())
        if not del_all:
            if count > len(chats):
                logger.error(f"Only {len(chats)} conversation fount")
            chats = chats[:count]

        async def del_conversation_no_exception(conversation_id):
            try:
                await self.delete_conversation(conversation_id)
            except Exception as e:
                logger.error(
                    f"Failed to delete conversation:{conversation_id} for the reason below:\n{e}"
                )

        tasks = []
        for chat in chats:
            tasks.append(del_conversation_no_exception(chat["conversationId"]))
        await asyncio.gather(*tasks)

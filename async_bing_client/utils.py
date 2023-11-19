from __future__ import annotations

import asyncio
import base64
import http.cookies
import json
import locale
import random
import sys
import urllib.parse
import uuid
from contextvars import copy_context
from datetime import datetime
from functools import wraps, partial
from io import BytesIO
from pathlib import Path
from typing import (
    TypeVar,
    Callable,
    Coroutine,
)
from typing import Union, Literal

import aiohttp
from PIL import Image, ImageOps
from typing_extensions import ParamSpec

from .const import ConversationStyle, LocationHint, IMAGE_HEADERS, FORWARDED_IP

P = ParamSpec("P")
R = TypeVar("R")


def parse_proxy_url(url: str):
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme
    hostname = parsed.hostname
    port = parsed.port
    username = parsed.username
    password = parsed.password
    if username and password:
        proxy_url = f"{scheme}://{username}:{password}@{hostname}:{port}"
    else:
        proxy_url = f"{scheme}://{hostname}:{port}"
    return proxy_url


def format_personality(personality: str):
    return (
        "".join(
            [
                ("-" + c if random.random() < 0.5 else "_" + c) if i > 0 else c
                for i, c in enumerate(
                    f"[system](#additional_instructions)\n{personality}\n\n"
                )
            ]
        )
        + "\n\n"
    )


def async_retry(max_retries):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            error = Exception("Unknown Error")
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    error = e
            await asyncio.sleep(1)
            raise Exception(f"Max Retry Exceed: {error}")

        return wrapper

    return decorator


def get_ran_hex(length: int = 32) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def guess_locale() -> str:
    if sys.platform.startswith("win"):
        return "en-us"
    loc, _ = locale.getlocale()
    if not loc:
        return "en-us"
    return loc.replace("_", "-")


def append_identifier(msg: dict) -> str:
    return json.dumps(msg, ensure_ascii=False) + "\x1e"


def run_sync(call: Callable[P, R]) -> Callable[P, Coroutine[None, None, R]]:
    """一个用于包装 sync function 为 async function 的装饰器

    参数:
        call: 被装饰的同步函数
    """

    @wraps(call)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_running_loop()
        pfunc = partial(call, *args, **kwargs)
        context = copy_context()
        result = await loop.run_in_executor(None, partial(context.run, pfunc))
        return result

    return _wrapper


@run_sync
def compress_image(infile: bytes) -> str:
    img = Image.open(BytesIO(infile))
    img = img.convert("RGB")
    size = len(infile)
    max_size = 1e6
    if size <= max_size:
        outfile = BytesIO()
        img.save(outfile, format="JPEG", quality=80, optimize=True)
        return base64.b64encode(outfile.getvalue()).decode("utf-8")
    else:
        ratio = (size / max_size) ** 0.6
        new_width = int(img.width / ratio)
        new_height = int(img.height / ratio)
        img = ImageOps.fit(img, (new_width, new_height), method=Image.LANCZOS)
        outfile = BytesIO()
        img.save(outfile, format="JPEG", quality=80, optimize=True)
        return base64.b64encode(outfile.getvalue()).decode("utf-8")


async def process_image_to_base64(image: str | bytes | Path):
    if isinstance(image, str):
        if Path(image).is_file():
            image = Path(image).read_bytes()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(image) as response:
                    image = await response.read()
    elif isinstance(image, Path):
        image = image.read_bytes()
    elif isinstance(image, bytes):
        pass
    else:
        raise TypeError("image must be str, Path, or bytes")

    return await compress_image(image)


def process_cookie(cookie: str | Path | list[dict]):
    def load_cookie_from_file(path: Union[str, Path]):
        with open(Path(path), "r") as f:
            return json.loads(f.read())

    if isinstance(cookie, (str, Path)):
        try:
            cookie_json = load_cookie_from_file(cookie)
        except Exception:
            try:
                cookie_json = json.loads(cookie)
            except Exception:
                raise ValueError("The cookie is not a valid path or json_schema")
    elif isinstance(cookie, list):
        cookie_json = cookie
    else:
        raise TypeError("The cookie must be a string, a Path, or a list of dicts")

    cookie_jar = aiohttp.CookieJar()

    for cookie_dict in cookie_json:
        morsel = http.cookies.Morsel()
        morsel.set(cookie_dict["name"], cookie_dict["value"], cookie_dict["value"])
        morsel["domain"] = cookie_dict["domain"]
        cookie_jar.update_cookies(
            http.cookies.SimpleCookie({cookie_dict["name"]: morsel})
        )

    return cookie_jar


def get_location_hint_from_locale(locale: str) -> Union[dict, None]:
    locale = locale.lower()
    if locale == "en-gb":
        hint = LocationHint.UK.value
    elif locale == "en-ie":
        hint = LocationHint.EU.value
    elif locale == "zh-cn":
        hint = LocationHint.CHINA.value
    else:
        hint = LocationHint.USA.value
    return hint.get("LocationHint")


async def build_chat_request(
    client,
    prompt: str,
    chat_data: dict,
    conversation_style: ConversationStyle
    | Literal["creative", "balanced", "precise"] = ConversationStyle.Precise,
    image: str | bytes | Path = None,
    personality=None,
    locale=guess_locale(),
):
    if "message" in chat_data.keys():
        is_start_of_conversation = False
    else:
        is_start_of_conversation = chat_data.get("isStart", True)

    if isinstance(conversation_style, str):
        conversation_style = getattr(ConversationStyle, conversation_style)

    options_set = conversation_style.value

    message_id = str(uuid.uuid4())

    timezone_offset = datetime.now() - datetime.utcnow()

    # Get the offset in hours and minutes
    offset_hours = int(timezone_offset.total_seconds() // 3600)
    offset_minutes = int((timezone_offset.total_seconds() % 3600) // 60)

    # Format the offset as a string
    offset_string = f"{offset_hours:+03d}:{offset_minutes:02d}"

    # Get current time
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + offset_string
    struct = {
        "arguments": [
            {
                "source": "cib",
                "optionsSets": options_set,
                "allowedMessageTypes": [
                    "ActionRequest",
                    "Chat",
                    "Context",
                    "InternalSearchQuery",
                    "InternalSearchResult",
                    "Disengaged",
                    "InternalLoaderMessage",
                    "Progress",
                    "RenderCardRequest",
                    "AdsQuery",
                    "SemanticSerp",
                    "GenerateContentQuery",
                    "SearchQuery",
                ],
                "sliceIds": [
                    "628ajcopus0",
                    "scdivetr",
                    "tts3cf",
                    "wrapuxslimc",
                    "gaincrrev",
                    "kcimgov2cf",
                    "0731ziv2s0",
                    "707enpcktrk",
                    "0518logos",
                    "0510wow",
                    "wowcds",
                    "727udtupm",
                    "815enftshrcs0",
                ],
                "verbosity": "verbose",
                "scenario": "SERP",
                "plugins": [],
                "traceId": str(get_ran_hex()),
                "isStartOfSession": is_start_of_conversation,
                "requestId": message_id,
                "message": {
                    "locale": locale,
                    "market": locale,
                    "region": str(locale[-2:]).upper(),
                    "location": "lat:47.639557;long:-122.128159;re=1000m;",
                    "locationHints": get_location_hint_from_locale(locale),
                    "userIpAddress": FORWARDED_IP,
                    "timestamp": timestamp,
                    "author": "user",
                    "inputMethod": "Keyboard",
                    "text": prompt,
                    "messageType": "Chat",
                    "messageId": message_id,
                    "requestId": message_id,
                },
                "tone": conversation_style.name.capitalize(),
                "spokenTextMode": "None",
                "conversationId": chat_data["conversationId"],
                "participant": {
                    "id": client.client_id,
                },
            },
        ],
        "invocationId": str(client.sent_times),
        "target": "chat",
        "type": 4,
    }
    conversation_signature = chat_data.get("conversationSignature")
    if conversation_signature:
        struct["arguments"][0]["conversationSignature"] = conversation_signature
    if image:
        blob_id = ""
        async with aiohttp.ClientSession(cookie_jar=client.cookie_jar) as session:
            img_base64 = await process_image_to_base64(image)

            writer = aiohttp.MultipartWriter()

            part_knowledge_request = writer.append(
                json.dumps(
                    {
                        "imageInfo": {},
                        "knowledgeRequest": {
                            "invokedSkills": ["ImageById"],
                            "subscriptionId": "Bing.Chat.Multimodal",
                            "invokedSkillsRequestData": {"enableFaceBlur": False},
                            "convoData": {
                                "convoid": chat_data["conversationId"],
                                "convotone": conversation_style.name,
                            },
                        },
                    }
                )
            )

            part_knowledge_request.set_content_disposition(
                "form-data", name="knowledgeRequest"
            )

            part_image_base64 = writer.append(img_base64)
            part_image_base64.set_content_disposition("form-data", name="imageBase64")

            async with session.post(
                "https://www.bing.com/images/kblob", headers=IMAGE_HEADERS, data=writer
            ) as response:
                if response.status != 200:
                    print(f"Status code: {response.status}")
                    text = await response.text()
                    print(text)
                    print(str(response.url))
                    raise Exception("Authentication failed")
                try:
                    response_json = await response.json()
                    blob_id = response_json["blobId"]
                except json.decoder.JSONDecodeError as exc:
                    text = await response.text()
                    print(text)
                    raise Exception("Authentication failed") from exc

        if blob_id:
            struct["arguments"][0]["message"]["imageUrl"] = (
                "https://www.bing.com/images/blob?bcid=" + blob_id
            )
            struct["arguments"][0]["message"]["originalImageUrl"] = (
                "https://www.bing.com/images/blob?bcid=" + blob_id
            )
    if personality and is_start_of_conversation:
        struct["arguments"][0]["previousMessages"] = [
            {
                "author": "user",
                "description": format_personality(personality),
                "contextType": "WebPage",
                "messageType": "Context",
                "messageId": "discover-web--page-ping-mriduna-----",
            },
        ]

    return struct

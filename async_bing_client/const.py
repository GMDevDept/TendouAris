import random
import uuid

from pydantic.types import Enum

FORWARDED_IP = (
    f"13.{random.randint(104, 107)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
)
HEADERS = {
    "Referer": "https://www.bing.com/search?q=Bing",
    "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    "Sec-Ch-Ua-Arch": '"x86"',
    "Sec-Ch-Ua-Bitness": '"64"',
    "Sec-Ch-Ua-Full-Version": '"115.0.5790.171"',
    "Sec-Ch-Ua-Full-Version-List": '"Not/A)Brand";v="99.0.0.0", "Google Chrome";v="115.0.5790.171", "Chromium";v="115.0.5790.171"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": "",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Ch-Ua-Platform-Version": '"15.0.0"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "X-Ms-Client-Request-Id": str(uuid.uuid4()),
    "X-Ms-Useragent": "azsdk-js-api-client-factory/1.0.0-beta.1 core-rest-pipeline/1.10.3 OS/Windows",
    "x-forwarded-for": FORWARDED_IP,
}
WSSHEADERS = {
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-websocket-extensions": "permessage-deflate; client_max_window_bits",
    "sec-websocket-key": "cwPgaMauiFR4WOfbbM0AJA==",
    "sec-websocket-version": "13",
    "x-forwarded-for": FORWARDED_IP,  # noqa: E501
}
DELETE_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "pragma": "no-cache",
    "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "referrer": "https://www.bing.com/",
    "referrerPolicy": "origin-when-cross-origin",
}

IMAGE_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "multipart/form-data; boundary=----WebKitFormBoundaryyO5cqct50HdHb9Qi",
    "pragma": "no-cache",
    "sec-ch-ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"115.0.5790.171"',
    "sec-ch-ua-full-version-list": '"Not/A)Brand";v="99.0.0.0", "Google Chrome";v="115.0.5790.171", "Chromium";v="115.0.5790.171"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "cookie": "cookie",
    "Referer": "https://www.bing.com/search?q=1",
    "Referrer-Policy": "origin-when-cross-origin",
}

DRAW_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"116.0.5845.141"',
    "sec-ch-ua-full-version-list": '"Chromium";v="116.0.5845.141", "Not)A;Brand";v="24.0.0.0", "Google Chrome";v="116.0.5845.141"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "iframe",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "Referer": "https://www.bing.com/search?q=Bing+Ai",
    "Referrer-Policy": "origin-when-cross-origin",
    "x-forwarded-for": FORWARDED_IP,
}


class ConversationStyle(Enum):
    Creative = [
        "nlu_direct_response_filter",
        "deepleo",
        "disable_emoji_spoken_text",
        "responsible_ai_policy_235",
        "enablemm",
        "dv3sugg",
        "autosave",
        "iyxapbing",
        "iycapbing",
        "h3imaginative",
        "enpcktrk",
        "logosv1",
        "udt4upm5gnd",
        "eredirecturl",
        "clgalileo",
        "gencontentv3",
    ]
    Balanced = [
        "nlu_direct_response_filter",
        "deepleo",
        "disable_emoji_spoken_text",
        "responsible_ai_policy_235",
        "enablemm",
        "dv3sugg",
        "autosave",
        "iyxapbing",
        "iycapbing",
        "galileo",
        "enpcktrk",
        "logosv1",
        "udt4upm5gnd",
        "eredirecturl",
        "saharagenconv5",
    ]
    Precise = [
        "nlu_direct_response_filter",
        "deepleo",
        "disable_emoji_spoken_text",
        "responsible_ai_policy_235",
        "enablemm",
        "dv3sugg",
        "autosave",
        "iyxapbing",
        "iycapbing",
        "h3precise",
        "enpcktrk",
        "logosv1",
        "udt4upm5gnd",
        "eredirecturl",
        "clgalileo",
        "gencontentv3",
        "gpt40613",
    ]


class LocationHint(Enum):
    USA = {
        "locale": "en-US",
        "LocationHint": [
            {
                "country": "United States",
                "state": "California",
                "city": "Los Angeles",
                "timezoneoffset": 8,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 34.0536909,
                    "Longitude": -118.242766,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }
    CHINA = {
        "locale": "zh-CN",
        "LocationHint": [
            {
                "country": "China",
                "state": "",
                "city": "Beijing",
                "timezoneoffset": 8,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 39.9042,
                    "Longitude": 116.4074,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }
    EU = {
        "locale": "en-IE",
        "LocationHint": [
            {
                "country": "Norway",
                "state": "",
                "city": "Oslo",
                "timezoneoffset": 1,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 59.9139,
                    "Longitude": 10.7522,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }
    UK = {
        "locale": "en-GB",
        "LocationHint": [
            {
                "country": "United Kingdom",
                "state": "",
                "city": "London",
                "timezoneoffset": 0,
                "countryConfidence": 8,
                "Center": {
                    "Latitude": 51.5074,
                    "Longitude": -0.1278,
                },
                "RegionType": 2,
                "SourceType": 1,
            },
        ],
    }

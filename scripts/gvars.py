import os

import redis
import google.generativeai as genai

from async_bing_client import Bing_Client
from async_claude_client import ClaudeAiClient

# Load env variables
bot_token = os.getenv("BOT_TOKEN")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
manager = [int(i) for i in os.getenv("MANAGER").split(",")]
whitelist = manager + [int(i) for i in os.getenv("WHITELIST").split(",")]
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
bard_1psid = os.getenv("BARD_1PSID")
bard_1psidts = os.getenv("BARD_1PSIDTS")
scope_global = os.getenv("SCOPE_GLOBAL")
scope_gemini = os.getenv("SCOPE_GEMINI")
scope_gpt35 = os.getenv("SCOPE_GPT35")
scope_gpt4 = os.getenv("SCOPE_GPT4")
scope_bing = os.getenv("SCOPE_BING")
scope_bard = os.getenv("SCOPE_BARD")
scope_claude = os.getenv("SCOPE_CLAUDE")
gemini_chatbot_close_delay = int(os.getenv("GEMINI_CHATBOT_CLOSE_DELAY_IN_GROUP"))
gpt35_chatbot_close_delay = int(os.getenv("GPT35_CHATBOT_CLOSE_DELAY_IN_GROUP"))
gpt4_chatbot_close_delay = int(os.getenv("GPT4_CHATBOT_CLOSE_DELAY"))
bing_chatbot_close_delay = int(os.getenv("BING_CHATBOT_CLOSE_DELAY"))
bard_chatbot_close_delay = int(os.getenv("BARD_CHATBOT_CLOSE_DELAY"))
claude_chatbot_close_delay = int(os.getenv("CLAUDE_CHATBOT_CLOSE_DELAY"))
flood_control_count = int(os.getenv("FLOOD_CONTROL_COUNT"))
flood_control_interval = int(os.getenv("FLOOD_CONTROL_INTERVAL"))

# Redis
db_chatdata = redis.Redis(host="arisdata", port=6379, db=0, decode_responses=True)

# In-memory cache
all_chats = {}  # {chat_id: ChatData}
gemini_addons = {}  # {preset_id: dict}
gpt35_addons = {}  # {preset_id: dict}
gpt4_addons = {}  # {preset_id: dict}

# Chatbot clients
genai.configure(api_key=google_api_key)
gemini_client = genai.GenerativeModel(
    "gemini-pro",
    generation_config={"temperature": 1},
    safety_settings=[
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ],
)

try:
    bing_client = Bing_Client(cookie="srv/bing_cookies.json")
except Exception:
    pass

try:
    claude_client = ClaudeAiClient(cookie="srv/claude_cookies.json")
except Exception:
    pass

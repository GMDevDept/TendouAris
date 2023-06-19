import os
import redis

# Load env variables
bot_token = os.getenv("BOT_TOKEN")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
manager = [int(i) for i in os.getenv("MANAGER").split(",")]
whitelist = manager + [int(i) for i in os.getenv("WHITELIST").split(",")]
openai_api_key = os.getenv("OPENAI_API_KEY")
google_bard_cookie = os.getenv("GOOGLE_BARD_COOKIE")
scope_global = os.getenv("SCOPE_GLOBAL")
scope_gpt35 = os.getenv("SCOPE_GPT35")
scope_gpt4 = os.getenv("SCOPE_GPT4")
scope_bing = os.getenv("SCOPE_BING")
scope_bard = os.getenv("SCOPE_BARD")
gpt35_chatbot_close_delay = int(os.getenv("GPT35_CHATBOT_CLOSE_DELAY_IN_GROUP"))
gpt4_chatbot_close_delay = int(os.getenv("GPT4_CHATBOT_CLOSE_DELAY"))
bing_chatbot_close_delay = int(os.getenv("BING_CHATBOT_CLOSE_DELAY"))
bard_chatbot_close_delay = int(os.getenv("BARD_CHATBOT_CLOSE_DELAY"))
flood_control_count = int(os.getenv("FLOOD_CONTROL_COUNT"))
flood_control_interval = int(os.getenv("FLOOD_CONTROL_INTERVAL"))

# Redis
db_chatdata = redis.Redis(host="arisdata", port=6379, db=0, decode_responses=True)

# In-memory cache
all_chats = {}  # {chat_id: ChatData}
gpt35_addons = {}  # {preset_id: dict}
gpt4_addons = {}  # {preset_id: dict}

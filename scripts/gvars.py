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
scope_bing = os.getenv("SCOPE_BING")
scope_bard = os.getenv("SCOPE_BARD")
gpt35_chatbot_close_delay = int(os.getenv("GPT35_CHATBOT_CLOSE_DELAY_IN_GROUP", 600))
bing_chatbot_close_delay = int(os.getenv("BING_CHATBOT_CLOSE_DELAY", 600))
bard_chatbot_close_delay = int(os.getenv("BARD_CHATBOT_CLOSE_DELAY", 600))

# Redis
db_chatdata = redis.Redis(host="arisdata", port=6379, db=0, decode_responses=True)

# In-memory cache
all_chats = {}  # {chat_id: ChatData}

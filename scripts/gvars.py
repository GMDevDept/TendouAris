import os
import redis

# Load env variables
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
manager = [int(i) for i in os.getenv("MANAGER").split(",")]
google_bard_cookie = os.getenv("GOOGLE_BARD_COOKIE", None)
bing_chatbot_close_delay = int(os.getenv("BING_CHATBOT_CLOSE_DELAY", 600))
bard_chatbot_close_delay = int(os.getenv("BARD_CHATBOT_CLOSE_DELAY", 600))

# Redis
db_chatdata = redis.Redis(host="arisdata", port=6379, db=0, decode_responses=True)

# In-memory cache
all_chats = {}  # {chat_id: ChatData}

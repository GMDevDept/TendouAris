import redis

db_chatdata = redis.Redis(host="arisdata", port=6379, db=0, decode_responses=True)

all_chats = {}  # {chat_id: ChatData}

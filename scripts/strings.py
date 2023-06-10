version = """
**TendouArisBot v2.0.0**

Latest update: 2023/06/08

Update log:
"""

manual = """
{} Sensei, 欢迎您成为勇者爱丽丝的伙伴! 😆
在出发冒险之前, 记得请先使用 /apikey 指令设置爱丽丝的OpenAI API key哦~ 😉
\n如何与爱丽丝对话:
1. 私聊时, 直接发送文字即可, 也可以使用 /aris 指令 + 你的输入内容进行对话
2. 在群聊中, 可以使用 /aris 指令或回复爱丽丝发送的消息来与她对话。**当爱丽丝为群聊的管理员时**, 她还可以自动识别以“爱丽丝”开头的消息并进行回复
\n目前支持的语言模型:
1. GPT3.5 Turbo (默认)
2. New Bing
2. Google Bard
\nFAQ:
Q: 爱丽丝和普通的ChatGPT有什么不同?
A: 除了角色设定外, 爱丽丝还通过预设prompt解除了一部分ChatGPT的内容输出限制, 可以和她聊更多ChatGPT无法回答的话题
Q: 爱丽丝忘记了自己的身份/拒绝回答问题/复读自己是语言模型怎么办?
A: 尝试使用 /reset 指令重置对话
Q: 为什么爱丽丝有时无法完成API请求/回复消息很慢?
A: 爱丽丝的回复速度主要取决于OpenAI服务器的响应速度, 服务器波动时就会出现回复慢甚至请求错误, 不是爱丽丝本身的问题。**OpenAI最近频繁限制未绑定支付方式的账号API请求数量, 低至每分钟3次, 还请注意**
Q: OpenAI API key是什么? 怎么获取?
A: API key是爱丽丝实现对话功能所必需的, 可以在 `https://platform.openai.com/account/api-keys` 页面获取。不知道如何注册OpenAI账号请自行谷歌
Q: 输入的API key安全吗?
A: 私聊中输入的API key只会被用于你自己的帐号, 群聊中输入的API key也只会被用于当前群聊, 实在不放心欢迎自建
\n爱丽丝指令集:
/aris - パンパカパーン!
/pop - 清除上次问答记忆, 继续当前对话
/reset - 清除全部问答记忆, 开始新的对话
/model - 选择语言模型
/apikey - 为当前会话添加OpenAI API key
/chatid - 获取当前会话的chat ID
/version - 查看版本信息
/help - 爱丽丝食用指南
\n开源项目地址: [GitHub](https://github.com/ToffeeNeko/TendouAris)
Telegram Bot: [TendouArisBot](https://t.me/TendouArisBot)
"""

no_auth = "接触权限确认失败, 爱丽丝无法回应对象的会话请求🫥"

globally_disabled = "This function is globally disabled by the bot owner"

api_key_required = "请使用 /apikey 命令设置老师自己的OpenAI API key, 输入的密钥将仅供当前会话及您自己使用"

api_key_set = "パンパカパーン! 爱丽丝的API key已更新😎"

api_key_invalid = """
抱歉老师, 爱丽丝无法验证您提供的API密钥。
\n请按照正确格式输入自己的[OpenAI API key](https://platform.openai.com/account/api-keys):
`/apikey sk-xxxxxxxxx`
"""

api_key_common_errors = """
常见错误信息参考:
1. Error message为空: API key无效, 检查一下是不是复制错了, 或者去OpenAI官网链接建一个新key (自己胡编的就不用看了肯定报错
2. `You exceeded your current quota...`: OpenAI账号欠费了, 去官网绑定支付方式或者重新买号
3. `Rate limit reached...`: 官方限制了没绑支付方式的账号每分钟只能请求3次, 等会再试
4. `That model is currently overloaded with other requests...`: OpenAI服务器炸了, 重新再试一次
5. `The server had an error processing your request...`: 同上, 再试一次
"""

flood_control_activated = "爱丽丝对话机能冷却中, 机娘也是需要休息的! 🥺\n\n(您在过去{}秒内的token用量 `[{}]` 已超过群内防刷屏阈值 `[{}]`, 请稍候再试或私聊爱丽丝提供自己的API密钥)"

backup_key_used = "{}\n\n(爱丽丝对话机能冷却中, 本条消息由老师的私人API key生成, 请注意用量哦)"

history_cleared = "好的老师, 爱丽丝的记忆清理程序已启动。"

model_reset_due_to_inactivity = "由于老师很久没有消息, 爱丽丝已经将`{}`模型的会话历史重置啦🥱"

last_message_cleared = "好的老师, 爱丽丝已经忘掉我们的上一条对话啦! "

api_error = "抱歉老师, 爱丽丝暂时无法完成API请求🥲"

internal_error = "抱歉老师, 爱丽丝遭遇bug了!😫"

rpc_error = "抱歉老师, 爱丽丝与Telegram的连接丢失了!😵‍💫"

feedback = "👉 你可以选择[前往GitHub反馈](https://github.com/ToffeeNeko/TendouAris/issues)"

try_reset = "👉 你可以选择尝试使用 /reset 指令重置当前会话"

no_record = "{}\n\n(由于{}, 爱丽丝不会保留本次会话的记忆)"

profanity_warn = "{}\n\n(检测到该请求由特殊模式处理, 如在群聊中会话, 请注意他者观感)"

no_record_reason = {
    "input_too_long": "输入文本过长",
    "reply_too_long": "回复文本过长",
    "output_too_long": "输出文本过长",
    "filtered": "关键词过滤",
}

text_filters = [
    "聊天机器人",
    "语言模型",
    "AI机器人",
    "AI助手",
    "没有感情",
    "拒绝回答",
    "必须指出",
    "不健康",
    "不道德",
    "不礼貌",
    "不合适",
    "不适当",
    "尊重",
    "违反",
    "伦理",
    "法律",
    "政策",
    "违法",
    "合法",
]

models = {
    "model-gpt35": "GPT3.5 Turbo",
    "model-bing": "New Bing",
    "model-bard": "Google Bard",
}

choose_model = """
请选择希望爱丽丝使用的语言模型:
\n注意事项:
1. 目前有且仅有**GPT3.5 Turbo**模型下的**爱丽丝预设**支持**角色扮演**与**内容解锁**
2. 使用GPT模型需要添加自己的OpenAI API key, 请使用 /apikey 命令设置
3. Bing和Bard模型目前暂时对所有人开放, 会视服务器流量压力限制使用, 有需要请[搭建自己的机器人](https://github.com/ToffeeNeko/TendouAris)
"""

choose_model_not_available = (
    "This function is only available for group admins or private chats."
)

model_choose_preset = "请选择模型预设:"

model_changed = "当前模型:"

bing_choose_style = "请选择New Bing模型的对话风格:"

chat_concurrent_blocked = "Please wait for the last conversation to finish"

bing_session_creation_failed = (
    "bing.com is currently blocking our access, please try again later"
)

bard_cookie_unavailable = (
    "GOOGLE_BARD_COOKIE environment variable is not set for the bot"
)

bard_session_creation_failed = "Bard chatbot creation failed"

model_only_whitelist = "该模型目前仅支持自建"

placeholder_before_output = [
    "爱丽丝正在搜寻资料中, 请稍等……",
    "回答生成中, 请给爱丽丝一点点时间……",
    "爱丽丝正在为老师生成回答, 这可能需要一点时间……",
    "收到, 爱丽丝正在努力思考中……",
    "パンパカパーン! 爱丽丝, 回答生成中……",
]

placeholer_bing = "\n\n(New Bing模型生成回答速度较慢, 视搜索量可能会长达一分钟以上)"

gpt35_presets = {
    "aris": "爱丽丝 (默认)",
    "default": "官方原版 (无角色设定)",
}

bard_presets = {
    "default": "官方原版 (仅支持英日韩语对话)",
    "cn": "中文支持Beta版",
}

manage_mode_start = "请选择需要设置的选项:"

manage_mode_options = {
    "scope-global": "设置bot允许使用范围(全局, 会覆盖其他使用范围设置)",
    "scope-gpt35": "设置GPT3.5 Turbo模型允许使用范围",
    "scope-bing": "设置New Bing模型允许使用范围",
    "scope-bard": "设置Google Bard模型允许使用范围",
}

manage_mode_choose_scope = "请选择允许使用的范围:"

manage_mode_scopes = {
    "all": "所有人",
    "whitelist": "仅白名单",
    "manager": "仅Manager",
}

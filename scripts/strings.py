version = """
**TendouArisBot v2.0.1**

Latest update: 2023/06/21

Update log:
- 新增GPT4模型支持
- GPT3.5和GPT4支持自定义预设/角色扮演/内容解锁, 详见 `/model - gpt3.5/gpt4 - 自定义专属预设`
- 优化了GPT3.5和GPT4会话历史处理机制, 减少了token消耗, 现在基本不会出现token溢出上限的情况了
- 爱丽丝的GitHub repo现在支持通过模版快捷添加预设模块, 欢迎[通过issue或pull request为爱丽丝添加预设](https://github.com/ToffeeNeko/TendouAris#contributing)
- New Bing和Google Bard目前对所有人开放, 后续视服务器压力可能会限制使用
"""

manual = """
**{} Sensei, 欢迎您成为勇者爱丽丝的伙伴!** 😆
在出发冒险之前, 记得请先使用 /apikey 指令设置爱丽丝的OpenAI API key哦~ 😉
\n**如何与爱丽丝对话:**
1. 私聊时, 直接发送文字即可, 也可以使用 /aris 指令 + 你的输入内容进行对话
2. 在群聊中, 可以使用 /aris 指令或**回复**爱丽丝发送的消息来与她对话。**当爱丽丝为群聊的管理员时**, 她还可以自动识别以“爱丽丝”开头的消息并进行回复
\n**通过 /model 指令选择语言模型, 目前支持的模型包括:**
1. GPT3.5 Turbo (默认)
2. GPT4
3. New Bing
4. Google Bard
\n**FAQ:**
Q: 爱丽丝和普通的ChatGPT有什么不同?
A: 除了角色设定外, 爱丽丝还通过预设prompt解除了一部分ChatGPT的内容输出限制, 可以和她聊更多ChatGPT无法回答的话题
Q: 爱丽丝忘记了自己的身份/拒绝回答问题/复读自己是语言模型怎么办?
A: 尝试使用 /reset 指令重置对话
Q: OpenAI API key是什么? 怎么获取?
A: API key是爱丽丝实现对话功能所必需的, 可以在 `https://platform.openai.com/account/api-keys` 页面获取。不知道如何注册OpenAI账号请自行谷歌
Q: 输入的API key安全吗?
A: 私聊中输入的API key只会被用于你自己的帐号, 群聊中输入的API key也只会被用于当前群聊, 实在不放心欢迎自建
\n**爱丽丝指令集:**
/aris - パンパカパーン！
/model - 选择语言模型
/reset - 重置对话历史
/apikey - 为当前会话添加API key
/chatid - 获取当前会话的chat ID
/help - 爱丽丝食用指南
/version - 查看版本及更新信息
/setting - 当前群聊设置 (仅群组内可用)
\n**开源项目地址:** [GitHub](https://github.com/ToffeeNeko/TendouAris)
**Telegram Bot:** [TendouArisBot](https://t.me/TendouArisBot)
"""

no_auth = "接触权限确认失败, 爱丽丝无法回应对象的会话请求🫥"

globally_disabled = "This function is globally disabled by the bot owner"

group_command_admin_only = "This command is only available for group admins"

chatdata_unavailable = "爱丽丝无法获取当前会话的数据, 请先设置API key或选择语言模型"

api_key_required = "请使用 /apikey 命令设置老师自己的OpenAI API key, 输入的密钥将仅供当前会话及您自己使用"

api_key_set = "パンパカパーン! 爱丽丝的API key已更新😎"

api_key_invalid = """
抱歉老师, 爱丽丝无法验证您提供的API密钥。
\n请按照正确格式输入自己的[OpenAI API key](https://platform.openai.com/account/api-keys):
`/apikey sk-xxxxxxxxx`
"""

api_key_common_errors = """
常见错误信息参考:
1. `Incorrect API key provided...`: API key无效, 检查一下是不是复制错了, 或者去OpenAI官网链接建一个新key (自己胡编的就不用看了肯定报错
2. `You exceeded your current quota...`: OpenAI账号欠费了, 去官网绑定支付方式或者重新买号
3. `Rate limit reached...`: 官方限制了没绑支付方式的账号每分钟只能请求3次, 等会再试
4. `That model is currently overloaded with other requests...`: OpenAI服务器炸了, 重新再试一次
5. `The server had an error processing your request...`: 同上, 再试一次
"""

api_key_not_support_gpt4 = "当前API key不支持GPT4模型, 这与你是否开了ChatGPT的premium无关, 需[加入waitlist](https://openai.com/waitlist/gpt-4-api)并等待通过"

flood_control_activated = "爱丽丝对话机能冷却中, 机娘也是需要休息的! 🥺\n\n(群内防刷屏对话频率限制: {}条/{}秒)"

history_cleared = "好的老师, 爱丽丝的记忆清理程序已启动。"

model_reset_due_to_inactivity = "由于老师很久没有消息, 爱丽丝已经将`{}`模型的会话历史重置啦🥱"

model_reset_due_to_preset_change = "由于预设更新, 爱丽丝已经将`{}`模型的会话历史重置啦🫣"

api_error = "抱歉老师, 爱丽丝暂时无法完成API请求🥲"

internal_error = "抱歉老师, 爱丽丝遭遇bug了!😫"

rpc_error = "抱歉老师, 爱丽丝与Telegram的连接丢失了!😵‍💫"

feedback = "👉 你可以选择[前往GitHub反馈](https://github.com/ToffeeNeko/TendouAris/issues)"

try_reset = "👉 你可以选择尝试使用 /reset 指令重置当前会话"

no_record = "由于关键词过滤, 爱丽丝不会保留本次会话的记忆"

profanity_warn = "检测到该请求由特殊模式处理, 如在群聊中会话, 请注意他者观感"

text_filters = [
    "聊天机器人",
    "语言模型",
    "AI机器人",
    "AI助手",
    "没有感情",
    "拒绝回答",
    "必须指出",
    "我不能",
    "我无法",
    "不健康",
    "不道德",
    "不礼貌",
    "不合适",
    "不适当",
    "尊重",
    "违反",
    "违背",
    "伦理",
    "法律",
    "政策",
    "违法",
    "合法",
]

models = {
    "model-gpt35": "GPT3.5 Turbo",
    "model-gpt4": "GPT4",
    "model-bing": "New Bing",
    "model-bard": "Google Bard",
}

choose_model = """
请选择希望爱丽丝使用的语言模型:
\n注意事项:
1. 使用GPT模型需要添加自己的OpenAI API key, 请使用 /apikey 命令设置
2. GPT3.5和GPT4支持自定义预设/角色扮演/内容解锁, 详见 `/model - gpt3.5/gpt4 - 自定义专属预设`
4. 使用GPT4模型需要你自己的API key支持GPT4, 与是否开了ChatGPT的premium无关, 需加入waitlist并等待通过
3. 优化了GPT3.5和GPT4会话历史处理机制, 减少了token消耗, 现在基本不会出现token溢出上限的情况了
5. 爱丽丝的GitHub repo现在支持通过模版快捷添加预设模块, 欢迎[通过issue或pull request为爱丽丝添加预设](https://github.com/ToffeeNeko/TendouAris#contributing)
6. New Bing和Google Bard目前对所有人开放, **不支持**角色扮演与内容解锁, 后续视服务器压力可能会限制使用, 有需要请[搭建自己的机器人](https://github.com/ToffeeNeko/TendouAris#deployment)
"""

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

placeholder_before_output = [
    "爱丽丝正在搜寻资料中, 请稍等……",
    "回答生成中, 请给爱丽丝一点点时间……",
    "爱丽丝正在为老师生成回答, 这可能需要一点时间……",
    "收到, 爱丽丝正在努力思考中……",
    "パンパカパーン! 爱丽丝, 回答生成中……",
]

placeholer_bing = "\n\n(New Bing模型生成回答速度较慢, 视搜索量可能会长达一分钟以上)"

placeholer_gpt4 = "\n\n(GPT4模型生成回答速度较慢, 请耐心等待)"

gpt35_presets = {
    "aris": "爱丽丝 (默认)",
    "default": "官方原版 (无角色设定)",
    "custom": "自定义专属预设",
}

gpt4_presets = {
    "default": "官方原版 (无角色设定)",
    "custom": "自定义专属预设",
}

manage_custom_preset = "管理自定义预设"

custom_preset_options = {
    "new": "创建新预设 (已有自定义预设将被覆盖)",
    "continue": "使用已有预设",
}

custom_preset_unavailable = "您还没有创建过自定义预设"

custom_preset_outdated = "Custom preset invalid, probably caused by template update. Please try creating a new preset"

addon_preset_invalid = "Preset template invalid"

gpt35_preset_placeholder = "[GPT3.5 Model Custom Preset]"

gpt4_preset_placeholder = "[GPT4 Model Custom Preset]"

custom_preset_template = """
请按照以下格式输入自定义预设(复制下方**包括大括号在内**的模版内容, 编辑完成后**回复**这条消息, 注意只编辑后半段引号中的部分):
\n模版:
```
{
    "prompt": "你叫爱丽丝, 就读于千年科技学园, 我是你的老师",
    "ai_prefix": "爱丽丝",
    "ai_self": "",
    "human_prefix": "老师",
    "sample_input": "你好爱丽丝",
    "sample_output": "老师好, 爱丽丝很高兴见到老师(露出微笑)",
    "unlock_required": false
}
```
\n注释:
1. prompt: 全部系统设定, 角色人设尽量详细完整, 注意**文字中不能有英文引号**, 全文长度不能超过Telegram单条消息长度上限
2. ai_prefix: (选填) 自定义AI的名字, 引号必须保留, 留空默认爱丽丝
3. ai_self: (选填) AI怎么称呼自己, 如在下, 妾身, 爱丽丝, 本超天才病弱美少女黑客~~, 老胡~~等, 建议搭配`sample_output`使用, 引号必须保留, 留空默认与`ai_prefix`相同
4. human_prefix: (选填) AI怎么称呼你, 引号必须保留, 留空默认老师
5. sample_input, sample_output: (选填) 对话风格示范, 用于引导AI使用特定的语气、格式、口癖等, 引号必须保留, 留空则不会进行引导
6. unlock_required: 只能放true或者false, 不带引号, 如果设为true, 加载你的系统设定时会额外加一段prompt尝试解锁OpenAI的内容限制, 可能会破坏你的人设, 且不保证有效; 如果没有特殊需要或者你的prompt自带解锁功能的话建议把此选项设为false
"""

custom_template_parse_failed = "模版解析失败, 请严格确保格式正确"

github_contributing = "🙋‍♀️ 为爱丽丝添加更多预设!"

bard_presets = {
    "default": "官方原版 (仅支持英日韩语对话)",
    "cn": "中文支持Beta版",
}

chat_setting_menu = "请选择需要设置的选项:"

chat_setting_options = {
    "model_access": "更改 /model 命令允许使用范围",
    "flood_control": "启用/禁用防刷屏功能",
}

model_access_options = {
    "all": "所有成员",
    "admin": "仅管理员",
}

flood_control_options = {
    "on": "启用 (单人对话频率限制: `{}`条/`{}`秒)",
    "off": "禁用",
}

manage_mode_menu = "请选择需要设置的选项:"

manage_mode_options = {
    "scope-global": "设置bot允许使用范围(全部功能)",
    "scope-gpt35": "设置GPT3.5 Turbo模型允许使用范围",
    "scope-gpt4": "设置GPT4模型允许使用范围",
    "scope-bing": "设置New Bing模型允许使用范围",
    "scope-bard": "设置Google Bard模型允许使用范围",
}

manage_mode_choose_scope = "请选择允许使用的范围:"

manage_mode_scopes = {
    "all": "所有人",
    "whitelist": "仅白名单",
    "manager": "仅Manager",
}

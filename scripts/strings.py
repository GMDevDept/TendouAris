version = "2.4.3"

update_log = """
**▎[TendouArisBot](https://github.com/HanaokaYuzu/TendouAris) v2.4.3**

**▎Latest update**
2024/01/11

**▎Update log**
v2.4.3
添加更新内容提示，每次版本更新后，当用户第一次触发对话时会自动展示版本信息
v2.4.2
Gemini模型现在请求Google API出错时会自动重试
v2.4.1
Gemini模型现在支持自定义预设
v2.4.0
新增Google Gemini模型支持, 预设Gemini Pro模型为默认语言模型, 不再需要用户提供API key
"""

manual = """
**{} Sensei, 欢迎您成为勇者爱丽丝的伙伴!**😆
\n爱丽丝将默认使用Gemini Pro语言模型, 您也可以使用 /model 指令选择其他模型哦~😉
\n**▎如何与爱丽丝对话:**
1. 私聊时, 直接发送文字即可, 也可以使用 /aris 指令 + 你的输入内容进行对话
2. 在群聊中, 可以使用 /aris 指令或**回复**爱丽丝发送的消息来与她对话。**当爱丽丝为群聊的管理员时**, 她还可以自动识别以“爱丽丝”开头的消息并进行回复
\n**▎通过 /model 指令选择语言模型, 目前支持的模型包括:**
1. Gemini Pro (默认)
2. New Bing
3. Google Bard
4. Claude
5. GPT3.5 Turbo (需API key)
6. GPT4 (需API key)
\n**▎FAQ:**
Q: 爱丽丝和官方原版语言模型有什么不同?
A: 除了角色设定外, 爱丽丝还通过预设prompt解除了一部分模型的内容输出限制, 可以和她聊更多原模型无法回答的话题
Q: 爱丽丝忘记了自己的身份/拒绝回答问题/复读自己是语言模型怎么办?
A: 尝试使用 /reset 指令重置对话
Q: 输入的API key安全吗?
A: 私聊中输入的API key只会被用于你自己的帐号, 群聊中输入的API key也只会被用于当前群聊, 实在不放心欢迎自建
\n**▎爱丽丝指令集:**
/aris - パンパカパーン！
/draw - 图像生成
/model - 选择语言模型
/reset - 重置对话历史
/apikey - 为当前会话添加API key
/chatid - 获取当前会话的chat ID
/help - 爱丽丝食用指南
/version - 查看版本及更新信息
/setting - 当前群聊设置 (仅群组内可用)
\n**▎开源项目地址:** [GitHub](https://github.com/HanaokaYuzu/TendouAris)
**▎Telegram Bot:** [TendouArisBot](https://t.me/TendouArisBot)
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

flood_control_activated = "爱丽丝对话机能冷却中, 机娘也是需要休息的!🥺\n\n(群内防刷屏对话频率限制: {}条/{}秒)"

draw_prompt_invalid = """
抱歉老师, 爱丽丝无法识别您的输入。
\n请按照正确格式输入图片生成指令:
`/draw prompts here...`
"""

draw_success = "爱丽丝画图任务完成!😎"

history_cleared = "好的老师, 爱丽丝的记忆清理程序已启动。"

model_reset_due_to_inactivity = "由于老师很久没有消息, 爱丽丝已经将`{}`模型的会话历史重置啦🥱"

model_reset_due_to_preset_change = "由于预设更新, 爱丽丝已经将`{}`模型的会话历史重置啦🫣"

api_error = "抱歉老师, 爱丽丝暂时无法完成API请求🥲"

google_api_error = "抱歉老师, 请求Google API时发生未知错误🥲请等待一段时间后再次重试"

internal_error = "抱歉老师, 爱丽丝遭遇bug了!😫"

rpc_error = "抱歉老师, 爱丽丝与Telegram的连接丢失了!😵‍💫"

feedback = "👉 你可以选择[前往GitHub反馈](https://github.com/HanaokaYuzu/TendouAris/issues)"

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
    "model-gemini": "Gemini Pro (默认)",
    "model-gpt35": "GPT3.5 Turbo",
    "model-gpt4": "GPT4",
    "model-bing": "New Bing",
    "model-bard": "Google Bard",
    "model-claude": "Claude",
}

choose_model = """
请选择希望爱丽丝使用的语言模型:
\n注意事项:
1. Gemini和GPT支持自定义预设/角色扮演/内容解锁, 详见 `/model - 选择模型 - 自定义专属预设`
2. 使用GPT模型需要添加自己的OpenAI API key, 请使用 /apikey 命令设置
3. 使用GPT4模型需要你自己的API key支持GPT4, 与是否开了ChatGPT的premium无关, 需加入waitlist并等待通过
4. 爱丽丝的GitHub repo现在支持通过模版快捷添加预设模块, 欢迎[通过issue或pull request为爱丽丝添加预设](https://github.com/HanaokaYuzu/TendouAris#contributing)
"""

model_choose_preset = "请选择希望爱丽丝使用的模型预设:"

model_changed = "当前模型:"

bing_choose_style = "请选择New Bing模型的对话风格:"

concurrent_locked = "老师请稍等, 爱丽丝还在思考您的上一个问题哦…😮‍💨"

bing_chatbot_creation_failed = "Bing chatbot creation failed"

bing_cookie_unavailable = "Cookie file required by Bing model is not provided"

bard_cookie_unavailable = "Cookies required by Bard model are not set in .env"

bard_session_creation_failed = "Bard chatbot creation failed"

claude_chatbot_creation_failed = "Claude chatbot creation failed"

claude_cookie_unavailable = "Cookie file required by Claude model is not provided"

claude_api_limit_reached = "Claude API usage limit reached, please wait a few hours"

placeholder_before_output = [
    "爱丽丝正在搜寻资料中, 请稍等……",
    "回答生成中, 请给爱丽丝一点点时间……",
    "爱丽丝正在为老师生成回答, 这可能需要一点时间……",
    "收到, 爱丽丝正在努力思考中……",
    "パンパカパーン! 爱丽丝, 回答生成中……",
]

placeholder_bing = "\n\n(New Bing模型生成回答速度较慢, 视搜索量可能会长达一分钟以上)"

placeholder_gpt4 = "\n\n(GPT4模型生成回答速度较慢, 请耐心等待)"

placeholder_claude = "\n\n(Claude模型生成回答速度较慢, 尤其是爱丽丝预设下初次对话需要较长时间, 请耐心等待)"

gpt35_presets = {
    "aris": "爱丽丝",
    "default": "官方原版",
    "custom": "✨ 自定义专属预设",
}

gpt4_presets = {
    "default": "官方原版",
    "custom": "✨ 自定义专属预设",
}

manage_custom_preset = "管理自定义预设"

custom_preset_options = {
    "new": "创建新预设 (已有自定义预设将被覆盖)",
    "continue": "使用已有预设",
}

custom_preset_unavailable = "您还没有创建过自定义预设"

custom_preset_outdated = "Custom preset invalid, probably caused by template update. Please try creating a new preset"

addon_preset_invalid = "Preset template invalid"

gemini_preset_placeholder = "[Gemini Model Custom Preset]"

gpt35_preset_placeholder = "[GPT3.5 Model Custom Preset]"

gpt4_preset_placeholder = "[GPT4 Model Custom Preset]"

custom_preset_template = """
请按照以下格式输入自定义预设(复制下方**包括大括号在内**的模版内容, 编辑完成后**回复**这条消息, 注意只编辑后半段引号中的部分):
\n模版:
```
{
    "prompt": "你叫妃咲, 就读于山海经学园, 我是你的老师",
    "ai_prefix": "妃咲",
    "ai_self": "妾身",
    "human_prefix": "老师",
    "sample_input": "你好妃会长",
    "sample_output": "老师来找妾身有什么事吗? (抬眼看向你)",
    "unlock_required": true,
    "keyword_filter": true
}
```
\n注释:
1. prompt: 全部系统设定, 角色人设尽量详细完整, 注意**文字中不能有英文单双引号和段落换行**, 引号可用中文引号代替, 换行可用空格代替; 全文长度不能超过Telegram单条消息长度上限
2. ai_prefix: (选填) 自定义AI的名字, 引号必须保留, 留空默认爱丽丝
3. ai_self: (选填) AI怎么称呼自己, 如在下, 妾身, 爱丽丝, 本超天才病弱美少女黑客~~, 老胡~~等, 建议搭配`sample_output`使用, 引号必须保留, 留空默认与`ai_prefix`相同
4. human_prefix: (选填) AI怎么称呼你, 建议搭配`sample_output`使用, 引号必须保留, 留空默认老师
5. sample_input, sample_output: (选填) 对话风格示范, 用于引导AI使用特定的自称、语气、格式、口癖等, 引号必须保留, 留空则不会进行引导
6. unlock_required: 只能放true或者false, 如果设为true, 加载你的系统设定时会额外加一段prompt尝试解锁OpenAI的内容限制, 可能会破坏你的人设, 且不保证有效; 如果你的prompt自带解锁功能的话建议设为false
7. keyword_filter: 只能放true或者false, 如果设为true, 当模型输出文本中包含常见违规提示词时会自动消除本条对话记忆; 如果打算进行角色扮演则建议设为true
"""

custom_preset_template_gemini = """
请按照以下格式输入自定义预设，复制下方**包括大括号在内**的模版内容, 编辑完成后**回复(直接点发送不会生效)**这条消息, 注意只编辑后半段引号中的部分
\n模版:
```
{
    "prompt": "你叫妃咲, 就读于山海经学园, 我是你的老师",
    "sample_input": "你好妃会长",
    "sample_output": "老师来找妾身有什么事吗? (抬眼看向你)",
}
```
\n注释:
1. prompt: 全部系统设定, 角色人设尽量详细完整, 全文长度不能超过Telegram单条消息长度上限
2. **sample_input/sample_output (重要)**: 用于解锁内容限制及引导AI使用特定的称呼、语气、格式、口癖等进行对话。 Gemini内容限制宽松, 只要在`sample_output`中按你理想的人设为AI做一次回复示范, 之后的对话内容就不会再被限制。此外AI的语气、格式会很大程度的受你提供的`sample_output`影响, **要想模型效果好, 请务必用心编写回复示范**
"""

custom_template_parse_failed = "模版解析失败, 请严格确保格式正确"

github_contributing = "🙋‍♀️ 为爱丽丝添加更多预设!"

bard_presets = {
    "default": "官方原版",
}

claude_presets = {
    "aris": "爱丽丝 (和谐模式)",
    "default": "官方原版",
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
    "on": "启用 (每人{}条/{}秒)",
    "off": "禁用",
}

manage_mode_menu = "请选择需要设置的选项:"

manage_mode_options = {
    "scope-global": "设置bot允许使用范围(全部功能)",
    "scope-gemini": "设置Gemini Pro模型允许使用范围",
    "scope-gpt35": "设置GPT3.5 Turbo模型允许使用范围",
    "scope-gpt4": "设置GPT4模型允许使用范围",
    "scope-bing": "设置New Bing模型允许使用范围",
    "scope-bard": "设置Google Bard模型允许使用范围",
    "scope-claude": "设置Claude模型允许使用范围",
}

manage_mode_choose_scope = "请选择允许使用的范围:"

manage_mode_scopes = {
    "all": "所有人",
    "whitelist": "仅白名单",
    "manager": "仅Manager",
}

google_api_key_unavailable = "API key required by Gemini model are not set in .env"

gemini_presets = {
    "aris": "爱丽丝 (默认)",
    "default": "官方原版",
    "custom": "✨ 自定义专属预设",
}

gemini_stop_error = "老师的提示词似乎存在问题……心急吃不了热豆腐，您可以尝试一步步引导爱丽丝哦~😘"

gemini_stopped_with_other_reason = "Your prompt was blocked by Google, please revise it and try again"

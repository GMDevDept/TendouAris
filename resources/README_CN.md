<p align="center">
    <img src="tendouaris.png" alt="Aris" width="500">
    <p/>
    <p align="center">
        <b><i>“欢迎老师。爱丽丝在等着老师。”</i></b>
    </p>
    <p align="center">
        <a href="../README.md">English</a> | <b>简体中文</b>
    </p>
    <p/>
</p>

# 天童爱丽丝

[![Telegram bot](https://img.shields.io/badge/bot-%40TendouArisBot-229ed9?logo=telegram&style=for-the-badge)](https://t.me/TendouArisBot)

## 介绍

爱丽丝是一个支持多种常见语言模型和客制化角色预设的 Telegram 聊天机器人。未来将添加对更多语言模型的支持。

| 模型名称 | 支持 | 自定义预设 | 图像输出 |
|:---:|:---:|:---:|:---:|
| Gemini Pro | ✅ | ✅ | 🚫 |
| gpt-3.5-turbo | ✅ | ✅ | 🚫 |
| gpt-4 | ✅ | ✅ | 🚫 |
| New Bing | ✅ | 🚫 | ✅ |
| Google Bard | ✅ | 🚫 | ✅ |
| Claude | ✅ | 🚫 | 🚫 |

注意：Bard模型输出的图片不是根据提示词自主生成的，它只能发送从Google搜索获取的现有图片。

## 贡献

爱丽丝支持从模板导入角色预设，这使得即使对没有编程基础的人来说，也很容易为她添加自己的角色预设。

您可以按照以下步骤操作来为爱丽丝添加自己的角色预设：

1. 在本地创建一个新的文本文件（.txt，.py等）。
2. 全选复制[预设模板](https://raw.githubusercontent.com/HanaokaYuzu/TendouAris/master/presets/template.py)中的内容，并将其粘贴到您刚刚创建的文本文件中。
3. 按照模板中的指示编辑您的提示词，就像您在Telegram机器人命令菜单中创建自己的自定义预设一样。如果有疑问，可以参考其他[当前可用的角色预设](https://github.com/HanaokaYuzu/TendouAris/tree/master/presets)。
4. 通过[新建Issue](https://github.com/HanaokaYuzu/TendouAris/issues/new)提交您的预设，可以附加文本文件（推荐）或将预设的内容粘贴到问题描述中。

如果您有编程经验，也可直接通过创建pull request来提交您的预设。只需将您的 `preset.py` 文件放在 `/presets` 目录下，并确保文件名与预设的 `id` 相同。

## 部署

1. 下载源代码并进入项目根目录。

    ``` bash
    git clone https://github.com/HanaokaYuzu/TendouAris.git
    cd TendouAris
    ```

2. 将项目根目录下的 `.env.sample` 文件重命名为 `.env` 并根据指示填写。
3. （可选）要启用Bing模型，请从 <https://bing.com/chat> 导出cookies并将其保存为 `\srv` 目录下的 `bing_cookies.json`。现有[模版](https://github.com/HanaokaYuzu/TendouAris/tree/master/srv/bing_cookies.sample.json)可供格式参考。
4. （可选）要启用Claude模型，请从 <https://claude.ai> 导出cookies并将其保存为 `\srv` 目录下的 `claude_cookies.json`。现有[模版](https://github.com/HanaokaYuzu/TendouAris/tree/master/srv/claude_cookies.sample.json)可供格式参考。
5. 构建docker容器。

    ``` bash
    docker-compose up -d --build
    docker image prune -f   # Remove unused dangling images (optional)
    ```

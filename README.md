<p align="center">
    <img src="resources/tendouaris.png" alt="Aris" width="500">
    <p align="center"></p>
    <p align="center">
        <b><i>“ようこそ先生。アリスは先生を待っていました。”</i></b>
    </p>
    <p align="center"></p>
</p>

# TendouAris

[![Telegram bot](https://img.shields.io/badge/bot-%40TendouArisBot-229ed9?logo=telegram&style=for-the-badge)](https://t.me/TendouArisBot)

## Introduction

Aris is a telegram chatbot based on OpenAI API with customized character preset. In the future will add support for more language models.

| Model Name | Support | Custom Prompt |
|:---:|:---:|:---:|
| gpt-3.5-turbo | ✅ | ✅ |
| gpt-4 | ✅ | ✅ |
| New Bing | ✅ | 🚫 |
| Google Bard | ✅ | 🚫 |
| Claude | ✅ | ✅ |

## Contributing

Aris supports importing add-on presets from template, which makes it pretty easy to contribute your own character preset to her, even for those who have no coding basis.

To add your own preset to Aris, follow the steps below:

1. Create a new text file (.txt, .py, etc.) on your local machine.
2. Copy texts from the [template](https://raw.githubusercontent.com/ToffeeNeko/TendouAris/master/presets/template.py) and paste it into the file you just created.
3. Edit your prompts following the instructions in the template, just like how you create your own custom preset using the bot's command menu in Telegram. Refer to other [currently available add-on presets](https://github.com/ToffeeNeko/TendouAris/tree/master/presets) if there's any confusion.
4. Submit your preset by [creating an issue](https://github.com/ToffeeNeko/TendouAris/issues/new), either attach the text file (recommended) or paste the content of your preset into the issue description.

Alternatively, if you have experience in git, you can also fork this repo and submit your preset by creating a pull request. Just put your `preset.py` file under `/presets` directory and make sure to the file name same as the `id` of the preset.

## Deployment

1. Download source code and go to project root directory.

    ``` bash
    git clone https://github.com/ToffeeNeko/TendouAris.git
    cd TendouAris
    ```

2. Rename .env.sample to .env and fill the values.
3. (Optional) To enable Bing model, export cookies from <https://bing.com/chat> and save it as `bing_cookies.json` under `\srv` directory. [Sample file](https://github.com/ToffeeNeko/TendouAris/tree/master/srv/bing_cookies.sample.json) is provided for format reference.
4. (Optional) To enable Claude model, export cookies from <https://claude.ai> and save it as `claude_cookies.json` under `\srv` directory. [Sample file](https://github.com/ToffeeNeko/TendouAris/tree/master/srv/claude_cookies.sample.json) is provided for format reference.
5. Build docker container.

    ``` bash
    docker-compose up -d --build
    docker image prune -f   # Remove unused dangling images (optional)
    ```

## Dependencies

- [Pyrogram](https://github.com/pyrogram/pyrogram): Elegant, modern and asynchronous Telegram MTProto API framework in Python for users and bots
- [LangChain](https://github.com/hwchase17/langchain): ⚡ Building applications with LLMs through composability ⚡
- [Async-Bing-Client](https://github.com/canxin121/Async-Bing-Client): async bing client for bing.com
- [Async-Claude-Client](https://github.com/canxin121/Async-Claude-Client): Async client for claude.ai and claude bot of slack
- [Bard](https://github.com/acheong08/Bard): Python SDK/API for reverse engineered Google Bard

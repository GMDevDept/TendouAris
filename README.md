<h1 align="center">
    <img width="500" src="resources/tendouaris.png" alt="Aris">
    <p align="left">TendouAris</p>
</h1>

[![Telegram bot](https://img.shields.io/badge/bot-%40TendouArisBot-229ed9?logo=telegram&style=for-the-badge)](https://t.me/TendouArisBot)

## Introduction

Aris is a telegram chatbot based on OpenAI API with customized system prompt. In the future will add support for more language models.

| Model Name | Support |
|:---:|:---:|
| gpt-3.5-turbo | ✅ |
| New Bing | ✅ |
| Google Bard | ✅ |

## Deployment

1. Download source code and go to project root directory

    ``` bash
    git clone https://github.com/ToffeeNeko/TendouAris.git
    cd TendouAris
    ```

2. Rename .env.sample to .env and fill in the values
3. Rename prompts.sample.py to prompts.py and fill in the values

4. (Optional) To enable New Bing language model, export cookie from bing.com to /srv/bing/cookies.json (sample provided for format reference)

5. Build docker container

    ``` bash
    docker-compose up -d --build
    docker image prune -f   # Remove unused dangling images (optional)
    ```

## Commands

You can copy the following commands and provide them to BotFather when building you own Aris.

1. Common commands

    ``` md
    aris - パンパカパーン！
    pop - 清除上次问答记忆，继续当前对话
    reset - 清除全部问答记忆，开始新的对话
    model - 选择语言模型
    apikey - 为当前会话添加OpenAI API key
    chatid - 获取当前会话的chat ID
    version - 查看版本信息
    help - 爱丽丝食用指南
    ```

2. Admin commands

    ``` md
    fapikey - 为指定的会话添加API key
    fctrl - 为指定的群组启用/禁用刷屏限制
    ```

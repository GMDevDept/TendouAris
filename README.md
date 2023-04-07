# TendouAris

## Deployment

1. ``` bash
    git clone https://github.com/ToffeeNeko/TendouAris.git
    cd TendouAris 
   ```

2. rename .env.sample to .env and fill in the values
3. rename prompts.sample.py to prompts.py and fill in the values

4. ``` bash
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
    apikey - 为当前对话添加OpenAI API key
    version - 查看版本信息
   ```

2. Admin commands

   ``` md
    fapikey - 为指定的对话添加API key
    fctrl - 为指定的群组启用/禁用刷屏限制
   ```

# project modules

from src.secretario_bot.telegram_messaging import SecretarioBot
from src.secretario_bot.enums import llm_models

# packages

import os
from dotenv import load_dotenv

# telegram bot

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

telegram_bot = SecretarioBot(bot_token=TOKEN, llm_model=llm_models.mistral_7b)
telegram_bot.run()

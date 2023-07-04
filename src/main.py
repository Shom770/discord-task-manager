from os import getenv

from dotenv import load_dotenv
from bot import TaskManagerBot

# Load the .env variables
load_dotenv()

# Deploy the bot
if __name__ == "__main__":
    bot_instance = TaskManagerBot()
    bot_instance.run(getenv("BOT_TOKEN"))

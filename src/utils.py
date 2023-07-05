from logging import getLogger
from os import getenv

from dotenv import load_dotenv
from notion_client import AsyncClient

load_dotenv()

discord_logger = getLogger("discord")
async_notion_client = AsyncClient(getenv("NOTION_TOKEN"))


class Constants:
    """Class that contains constants which the bot relies on."""
    APPLICATION_ID = 1125900085314715708
    GUILD_ID = 1125903298646515783

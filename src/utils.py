from logging import getLogger
from os import getenv

from dotenv import load_dotenv
from notion_client import AsyncClient

load_dotenv()

discord_logger = getLogger("discord")
notion = AsyncClient(auth=getenv("NOTION_TOKEN"))


class Constants:
    """Class that contains constants which the bot relies on."""
    APPLICATION_ID = 1125900085314715708
    GUILD_ID = 1125903298646515783
    DATABASE_ID = "9ccad614d81e4f2ea561334bc0b7116c"

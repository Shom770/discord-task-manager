import discord
from discord.ext import commands

from utils import async_notion_client, Constants


class ChannelCreator(commands.Cog):
    """Creates channels for the different classes that a task can be assigned to in the Notion database."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Used to create the channels based on the different classes in the database if they don't already exist."""
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(
        ChannelCreator(bot),
        guilds=[discord.Object(Constants.GUILD_ID)]
    )

import discord
from discord.ext import commands

from utils import Constants, discord_logger


class TaskManagerBot(commands.Bot):
    """Class that extends off of discord.py's Bot class to add additional functionalities and load cogs."""

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            application_id=Constants.APPLICATION_ID
        )

    async def setup_hook(self) -> None:
        """Used to load all the cogs into the bot."""
        await self.load_extension("cogs.channel_creator")
        await self.load_extension("cogs.task_creator")
        await self.load_extension("cogs.assignments_to_tasks")

        await self.tree.sync(guild=discord.Object(Constants.GUILD_ID))

    async def on_ready(self) -> None:
        """Used for debugging purposes when deploying the bot."""
        discord_logger.info(f"{self.user} has connected to the guild!")

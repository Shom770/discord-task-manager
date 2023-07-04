import discord
from discord.ext import commands

from utils.constants import Constants


class TaskManagerBot(commands.Bot):
    """Class that extends off of discord.py's Bot class to add additional functionalities and load cogs."""

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            application_id=Constants.APPLICATION_ID
        )

    async def on_ready(self):
        """Used for debugging purposes when deploying the bot."""
        print(f"{self.user} has connected to the guild!")

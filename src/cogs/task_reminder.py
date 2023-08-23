from datetime import datetime

import discord
from discord import Color, Embed
from discord.ext import commands, tasks

from utils import Constants, DateTransformer, discord_logger, NotionWrapper


class TaskReminder(commands.Cog):
    """Reminds the user about the tasks that are due soon in the Notion database."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @tasks.loop(hours=24)
    async def send_reminders(self) -> None:
        """Used to remind the user about overdue tasks and upcoming tasks."""
        notion_wrapper = await NotionWrapper.create()
        database_tasks = await notion_wrapper.retrieve_all_tasks()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Start the task to remind the user about upcoming and overdue tasks."""
        self.send_reminders.start()


async def setup(bot: commands.Bot):
    await bot.add_cog(
        TaskReminder(bot),
        guilds=[discord.Object(Constants.GUILD_ID)]
    )

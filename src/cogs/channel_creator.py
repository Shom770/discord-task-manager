import discord
from discord.ext import commands, tasks

from utils import Constants, discord_logger, NotionWrapper


class ChannelCreator(commands.Cog):
    """Creates channels for the different classes that a task can be assigned to in the Notion database."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @tasks.loop(hours=24)
    async def create_channels(self) -> None:
        """Used to create the channels based on the different classes in the database if they don't already exist."""
        notion_wrapper = await NotionWrapper.create()
        classes = [
            class_name.replace(" ", "-").replace("&", "").lower()  # Turn into the format Discord uses for channel names
            for class_name in notion_wrapper.properties["Class"].names()
        ]

        guild = self.bot.guilds[0]
        task_updater_category = discord.utils.get(guild.categories, id=1125906531603464225)
        current_channels = [channel.name for channel in task_updater_category.text_channels]

        # Recreate channels if the class property changed in the task list.
        if (
            [
                class_name.split("-")[0] for class_name in classes  # Avoid finding differences in emojis
            ] != [
                class_name.split("-")[0] for class_name in current_channels
            ]
        ):
            discord_logger.info("Change found in the classes within the task list -- recreating channels.")

            # Delete current channels if there are any
            for channel in task_updater_category.text_channels:
                await channel.delete()

            # Create the new channels under the new select types in the Class property
            for channel_name in classes:
                await guild.create_text_channel(channel_name, category=task_updater_category)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Start the task to create the channels based on the current classes in the Notion database."""
        self.create_channels.start()


async def setup(bot: commands.Bot):
    await bot.add_cog(
        ChannelCreator(bot),
        guilds=[discord.Object(Constants.GUILD_ID)]
    )

from datetime import datetime

import discord
from discord import app_commands, Color, Embed
from discord.ext import commands

from utils import Constants, DateTransformer, discord_logger, NotionWrapper


class TaskCreator(commands.Cog):
    """Allows users to create a task into their Notion database from Discord."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.notion_wrapper = None  # Defined later

    @app_commands.command()
    async def create_task(
        self,
        interaction: discord.Interaction,
        name: str,
        date: app_commands.Transform[datetime, DateTransformer],
        type_of_task: str
    ):
        if not self.notion_wrapper:
            self.notion_wrapper = await NotionWrapper.create()

        # Convert the channel name to the according class in the Notion database.
        class_name = interaction.channel.name.replace("-", " ").capitalize()

        await self.notion_wrapper.create_page(
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": name
                            }
                        }
                    ]
                },
                "Due Date": {
                    "date": {
                        "start": date.strftime("%Y-%m-%d")  # Convert to ISO format
                    }
                },
                "Class": {
                    "select": {
                        "name": class_name
                    }
                },
                "Type": {
                    "select": {
                        "name": type_of_task
                    }
                }
            }
        )

        await interaction.response.send_message(
            embed=Embed(
                title="Task created successfully!",
                description=f"Your task: {name!r} for {class_name.split()[0]} was successfully created.",
                color=Color.green()
            ),
            ephemeral=True
        )

    @create_task.autocomplete("type_of_task")
    async def type_of_task_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        if not self.notion_wrapper:
            self.notion_wrapper = await NotionWrapper.create()

        return [
            app_commands.Choice(name=class_name, value=class_name)
            for class_name in self.notion_wrapper.properties["Type"].names() if current.lower() in class_name.lower()
        ]


async def setup(bot: commands.Bot):
    await bot.add_cog(
        TaskCreator(bot),
        guilds=[discord.Object(Constants.GUILD_ID)]
    )
    
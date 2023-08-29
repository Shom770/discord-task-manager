import discord
from discord import Color, Embed
from discord.ext import commands, tasks

from utils import CanvasWrapper, Constants, discord_logger, NotionWrapper


class AssignmentToTasks(commands.Cog):
    """Creates tasks in the Notion database based on the assignments from Canvas."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @tasks.loop(hours=24)
    async def pull_assignments(self) -> None:
        """Used to create the channels based on the different classes in the database if they don't already exist."""
        notion_wrapper = await NotionWrapper.create()
        canvas_wrapper = CanvasWrapper()

        # Retrieve the current assignments and filter out assignments if they already exist as a task
        existing_task_names = {task.name for task in await notion_wrapper.retrieve_all_tasks()}
        relevant_assignments = {
            class_name: [assignment for assignment in assignments if assignment.name not in existing_task_names]
            for class_name, assignments in canvas_wrapper.assignments_by_course().items()
        }

        # Create the tasks for the assignments
        total_assignments = 0

        for class_name, assignments in relevant_assignments.items():
            shortened_name = class_name.split()

            try:
                class_name_in_notion = Constants.CANVAS_TO_NOTION[" ".join(shortened_name[:-1])]
            except KeyError:  # Handle when a teacher has spaces in their name
                class_name_in_notion = Constants.CANVAS_TO_NOTION[" ".join(shortened_name[:-2])]

            for assignment in assignments:
                await notion_wrapper.create_page(
                    properties={
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": assignment.name
                                    }
                                }
                            ]
                        },
                        "Due Date": {
                            "date": {
                                "start": assignment.due_date.strftime("%Y-%m-%d")  # Convert to ISO format
                            }
                        },
                        "Class": {
                            "select": {
                                "name": class_name_in_notion
                            }
                        },
                        "Type": {
                            "select": {
                                "name": "Assignment"  # Default choice
                            }
                        }
                    }
                )

            discord_logger.info(f"Finished adding {len(assignments)} assignments for {class_name_in_notion}")
            total_assignments += len(assignments)

        # Send message informing user about the new tasks
        logs_channel = self.bot.get_channel(1145913948378497065)
        await logs_channel.send(
            embed=Embed(title=f"Added {total_assignments} assignments to your task board.", color=Color.green())
        )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Start the task to create the channels based on the current classes in the Notion database."""
        self.pull_assignments.start()


async def setup(bot: commands.Bot):
    await bot.add_cog(
        AssignmentToTasks(bot),
        guilds=[discord.Object(Constants.GUILD_ID)]
    )

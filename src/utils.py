from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from operator import itemgetter
from os import getenv

from canvasapi import Canvas
from discord import app_commands, Interaction
from dotenv import load_dotenv
from notion_client import AsyncClient

load_dotenv()

discord_logger = getLogger("discord")


class Constants:
    """Class that contains constants which the bot relies on."""
    APPLICATION_ID = 1125900085314715708
    GUILD_ID = 1125903298646515783
    DATABASE_ID = "9ccad614d81e4f2ea561334bc0b7116c"
    CANVAS_TO_NOTION = {
        "Adv Sci3 Earth SpSys": "ESS 🌋",
        "Adv Sci4 Biology": "Biology 🧪",
        "Algorithm Data": "Computer Science 💻",
        "AP US History": "APUSH ⚖️",
        "Found Of Tech": "FOT 🪚",
        "Mag Precalculus": "Precalculus 📐",
        "Hon English": "English 📖",
        "Hon Spanish": "Spanish 🌎"
    }


@dataclass
class Task:
    """A dataclass used to represent a task in the Notion database in a more readable format."""

    name: str
    due_date: datetime
    type_of_assignment: str
    class_name: str
    is_completed: bool

    def is_overdue(self) -> bool:
        """Compares the current time to the due date of the task and checks if it's overdue, using `days_overdue`."""
        return self.days_overdue() > 0 and not self.is_completed

    def days_overdue(self) -> int:
        """Returns the amount of days a task is overdue."""
        return (datetime.now() - self.due_date).days


@dataclass
class Assignment:
    """A dataclass used to represent an assignment from Canvas."""

    name: str
    due_date: datetime | None
    points_possible: float


class NotionProperty:
    """A class used to describe different properties of a Notion database for simplicity and abstraction."""

    def __init__(self, name: str, type: str, **kwargs):
        self.name = name
        self.property_type = type
        self.property_options = kwargs[type].get("options", [])

    def names(self) -> list:
        """Returns the names of each option in the property (only for select and multi-select)."""
        return [option_name for option in self.property_options if (option_name := option.get("name"))]


class NotionWrapper:
    """A wrapper around `AsyncClient` to provide more custom functionality regarding the Notion database."""

    def __init__(self, client: AsyncClient, database_info: dict, database_id: str) -> None:
        self.client = client
        self.database_info = database_info
        self.database_id = database_id

    @classmethod
    async def create(cls, database_id: str = Constants.DATABASE_ID) -> "NotionWrapper":
        """An alternate constructor to set up the Notion client to be used."""
        new_client = AsyncClient(auth=getenv("NOTION_TOKEN"))

        return NotionWrapper(
            client=new_client,
            database_info=(await new_client.databases.retrieve(database_id=database_id)),
            database_id=database_id
        )

    @property
    def properties(self) -> dict:
        return {
            name: NotionProperty(**property)
            for name, property in self.database_info["properties"].items()
        }

    async def create_page(
        self,
        properties: dict
    ) -> None:
        """Creates a page in the according database using the Notion API."""
        await self.client.pages.create(
            parent={
                "type": "database_id",
                "database_id": self.database_id
            },
            properties=properties
        )

    async def retrieve_all_tasks(self) -> list[Task]:
        """Retrieves all of the tasks listed in the according database using the Notion API."""
        task_dict = await self.client.databases.query(database_id=self.database_id)
        task_results = task_dict.get("results")

        # Paginate through all the different tasks
        while task_dict.get("has_more"):
            task_dict = await self.client.databases.query(
                database_id=self.database_id,
                start_cursor=task_dict["next_cursor"]
            )
            if task_dict.get("results"):
                task_results.extend(task_dict.get("results"))

        return [
            Task(
                name=task["properties"]["Name"]["title"][0]["text"]["content"],
                due_date=datetime.strptime(
                    (task["properties"]["Due Date"]["date"] or {}).get("start", datetime.today().strftime("%Y-%m-%d")).split("T")[0],
                    "%Y-%m-%d"
                ),
                type_of_assignment=(task["properties"]["Type"]["select"] or {}).get("name"),
                class_name=(task["properties"]["Class"]["select"] or {}).get("name"),
                is_completed=task["properties"]["Status"]["status"].get("name", "").lower() == "completed"
            )
            for task in task_results
        ]


class CanvasWrapper:
    """A synchronous wrapper around the Canvas API for the specific purposes of this bot."""
    def __init__(self) -> None:
        self._client = Canvas("https://mcpsmd.instructure.com", getenv("CANVAS_TOKEN"))
        self.account = self._client.get_current_user()
        self._courses = self.account.get_courses()

        # Find the current courses that are relevant to the use of the Canvas API.
        courses_by_date = [
            (course, datetime.now() - datetime.fromisoformat(course.created_at.removesuffix("Z")))
            for course in self._courses
            if not hasattr(course, "access_restricted_by_date")
        ]
        _, latest_creation_date = min(courses_by_date, key=itemgetter(1))
        self.active_courses = [
            course for course, days_since_created in courses_by_date
            if days_since_created.days == latest_creation_date.days
        ]

    def assignments_by_course(self) -> dict[str, list[Assignment]]:
        """Returns a dictionary containing the course name and the assignments for that course."""
        assignments = {}

        for course in self.active_courses:
            assignments[course.name] = []

            for assignment in course.get_assignments():
                # Skip assignments that don't grant any points or have no due date
                if not assignment.points_possible or assignment.due_at is None:
                    continue

                due_date = datetime.fromisoformat(assignment.due_at.removesuffix("Z"))

                # Skip assignments that are due in more than two weeks or were due before today.
                if (delta := due_date - datetime.now()).days >= 14 or delta.days < 0:
                    continue

                assignments[course.name].append(
                    Assignment(
                        assignment.name.removeprefix("(NR)").removeprefix("(R)").strip(),
                        datetime.fromisoformat(assignment.due_at.removesuffix("Z")),
                        assignment.points_possible
                    )
                )

        return assignments


class DateTransformer(app_commands.Transformer):
    """Converts a string to a datetime object (in the format of MM/DD/YYYY)"""

    async def transform(self, interaction: Interaction, value: str) -> datetime:
        """The main method used to convert a string into a datetime object."""
        # Pad each value with zeros before formatting
        formatted_date = "/".join(part.zfill(2) if len(part) <= 2 else part for part in value.split("/"))

        # Parse the argument into a time
        return datetime.strptime(formatted_date, "%m/%d/%y")
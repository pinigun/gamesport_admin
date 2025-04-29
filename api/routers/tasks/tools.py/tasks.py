from api.routers.tasks.schemas import TasksData
from database import db


class TasksTools:
    async def get_tasks() -> list[TasksData]:
        return [
            TasksData.model_validate(dict(task))
            for task in await db.tasks.get_all()
        ] 
from api.routers.tasks.schemas import Task, TasksData
from database import db


class TasksTools:
    async def get_all() -> list[TasksData]:
        return [
            Task.model_validate(dict(task))
            for task in await db.tasks.get_all()
        ] 
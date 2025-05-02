import io
from fastapi import HTTPException
from jedi.inference import value
import pandas as pd
from api.routers.tasks.schemas import SupportedGiveaway, Task, TaskParticipant, TasksData
from database import db
from database.exceptions import CustomDBExceptions
from tools.photos import PhotoTools


class TasksTools:
    async def update(
        task_id: int,   
        **new_task_data
    ):
        photo = new_task_data.pop('photo', None)
        
        new_task_data['active'] = new_task_data.pop('is_active')
        new_task_data['tickets'] = new_task_data.pop('reward')
        new_task_data['big_descr'] = new_task_data.pop('description')
        
        if photo:
            new_task_data['photo'] = await PhotoTools.save_photo(path=f'static/tasks/{task_id}', photo=photo)

        await db.tasks.update(
            task_id=task_id,
            **{key: value for key, value in new_task_data.items() if value is not None},
        )
        new_info = (await db.tasks.get_all(page=1, per_page=1, task_id=task_id))[0]
        return Task(**new_info)
    
    
    async def add(    
        **new_task_data
    ):
        photo = new_task_data.pop('photo', None)
        
        new_task_data['active'] = new_task_data.pop('is_active')
        new_task_data['tickets'] = new_task_data.pop('reward')
        new_task_data['big_descr'] = new_task_data.pop('description')
        
        # Добавляем юзера чтобы получить id
        new_task = await db.tasks.add(**new_task_data)
        if photo:        
            photo_path = await PhotoTools.save_photo(path=f'static/tasks/{new_task.id}', photo=photo)
            await db.tasks.update(
                task_id=new_task.id,
                photo=photo_path
            )
        new_info = (await db.tasks.get_all(page=1, per_page=1, task_id=new_task.id))[0]
        return Task(**new_info)
    
    
    async def get_all(page: int, per_page: int, task_id: int | None, name: str | None) -> list[TasksData]:
        return [
            Task.model_validate(dict(task))
            for task in await db.tasks.get_all(
                page=page,
                per_page=per_page,
                task_id=task_id,
                name=name
            ) 
        ] 
        
    
    async def get_count() -> int:
        return await db.tasks.get_count()
    
    
    async def get_participants(task_id: int) -> list[TaskParticipant]:
        return [
            TaskParticipant.model_validate(participant)
            for participant in await db.tasks.get_participants(task_id)
        ]
        
    
    async def get_participants_report(participants: list[TaskParticipant]):
        if len(participants) > 0:    
            df = pd.DataFrame([row.model_dump() for row in participants])
        else:
            # Создаем DataFrame с колонками из Pydantic-модели
            df = pd.DataFrame(columns=TaskParticipant.model_fields.keys())
        # Записываем в память (в буфер)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)  # возвращаемся в начало буфера

        # Отправляем как файл
        return output
    
    
    async def get_supported_giveaways() -> list[SupportedGiveaway]:
        return [
            SupportedGiveaway.model_validate(sup_giv)
            for sup_giv in await db.tasks.get_supported_giveaways()
        ]
    
    
    async def delete(task_id):
        await db.tasks.delete(task_id)
        await PhotoTools.delete(path=f"static/tasks/{task_id}")

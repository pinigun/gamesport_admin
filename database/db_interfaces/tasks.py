from database.db_interface import BaseInterface
from sqlalchemy import text

from database.models import TaskTemplate


class TasksDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
    
    
    async def update(self, task_id: int, **new_task_data):
        return await self.update_rows(
            TaskTemplate,
            filter_by={'id': task_id},
            **new_task_data
        )
    
    
    async def add(self, **new_task_data):
        return await self.add_row(
            TaskTemplate,
            **new_task_data
        )
    
    
    async def get_all(self, page: int, per_page: int, task_id: int | None = None):
        async with self.async_ses() as session:
            query = '''
            with users_completed_tasks AS (
                    SELECT
                        utc.task_template_id,
                        utc.user_id, 
                        COUNT(utc.user_id) AS user_completed
                    FROM user_tasks_complete utc 
                    JOIN tasks_templates tt ON tt.id = utc.task_template_id
                    GROUP BY utc.task_template_id, utc.user_id
                ), tasks_count AS (
                    SELECT uct.user_id, uct.task_template_id, uct.user_completed, tt.complete_count
                    FROM users_completed_tasks uct
                    JOIN tasks_templates tt ON tt.id = uct.task_template_id
                ),
                fully_completed_tasks as (
                    select 
                        uct.task_template_id,
                        count(uct.task_template_id) as fully_completed_tasks
                    from 
                        tasks_count uct
                    where 
                        uct.user_completed=uct.complete_count 
                    group by 
                        uct.task_template_id 
                ),
                started_tasks as (
                    select 
                        uct.task_template_id,
                        count(uct.task_template_id) as started_tasks
                    from 
                        tasks_count uct
                    where 
                        uct.user_completed<>uct.complete_count 
                    group by 
                        uct.task_template_id 
                )
                select
                tt.id,
                tt.created_at,
                tt.title,
                tt.tickets as reward,
                tt.active as is_active,
                coalesce(fct.fully_completed_tasks, 0) as completed,
                coalesce(sct.started_tasks, 0) as started,
                tt.check_type,
                tt.photo
                from tasks_templates tt
                left join fully_completed_tasks fct on fct.task_template_id = tt.id 
                left join started_tasks sct on sct.task_template_id = tt.id
            '''
            if task_id:
                query += f' WHERE tt.id = {task_id}'
                
            query += '''
                offset :offset
                limit :limit;
            '''
            if task_id:
                result = await session.execute(text(query), {'offset': (page-1)*per_page, 'limit': per_page})
                return result.mappings().first()
            result = await session.execute(text(query), {'offset': (page-1)*per_page, 'limit': per_page})
            return result.mappings().all()
        
    async def get_count(self) -> int:
        return await self.get_rows_count(
            TaskTemplate
        )
        
    
    async def get_participants(self, task_id: int):
        async with self.async_ses() as session:
            query = '''
            with task_participants as (
                select
                    utc.task_template_id as task_id,
                    utc.user_id,
                    count(utc.user_id) completed_tasks
                from 
                    user_tasks_complete utc
                left join users u on u.id = utc.user_id
                where utc.task_template_id = :task_id
                group by user_id, utc.task_template_id
            )
            select 
                tp.*,
                u.email,
                u.phone,
                u.username as tg_username,
                u.tg_id,
                (
                case
                    when tp.completed_tasks = tt.complete_count then true
                    else false
                end
                ) as completed
            from task_participants tp
            join users u on u.id = tp.user_id
            join tasks_templates tt on tt.id = tp.task_id
            '''
            result = await session.execute(
                text(query), params={'task_id': task_id}
            )
            return result.mappings().all()
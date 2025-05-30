from database.db_interface import BaseInterface
from sqlalchemy import text

from database.models import Giveaway, TaskTemplate


class TasksDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
    
    
    async def get(self, task_id: int):
        return (await self.get_all(page=1, per_page=1, task_id=task_id))
    
     
    async def delete(self, task_id: int):
        await self.delete_rows(TaskTemplate, id=task_id)   
        
        
    async def get_supported_giveaways(self):
        return await self.get_rows(Giveaway, streamname=None)
        
    
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
    
    
    async def get_all(
        self,
        page: int,
        per_page: int,
        order_by: str = 'task_id',
        order_direction: str = 'desc',
        task_id: int | None = None,
        name: str | None = None
    ):
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
                    tt.big_descr as description,
                    tt.tickets as reward,
                    tt.active as is_active,
                    tt.gift_giveaway_id as giveaway_id,
                    tt.postback_url as postback_url,
                    tt.redirect_url,
                    tt.timer_value as timer,
                    coalesce(fct.fully_completed_tasks, 0) as completed,
                    coalesce(sct.started_tasks, 0) as started,
                    tt.check_type,
                    tt.photo
                from 
                    tasks_templates tt
                left join 
                    fully_completed_tasks fct 
                    on 
                    fct.task_template_id = tt.id 
                left join 
                    started_tasks sct 
                    on 
                    sct.task_template_id = tt.id
            '''
            
            params = {'offset': (page-1)*per_page, 'limit': per_page}
            if task_id:
                query += f' WHERE tt.id = :task_id'
                params['task_id'] = task_id
            elif name:
                query += f' WHERE tt.title ILIKE :name_pattern'
                params['name_pattern'] = f"%{name}%"
            
            match order_by:
                case 'task_id':
                    order_by='tt.id'
                case 'status':
                    order_by='tt.active'
                case _:
                    order_by='tt.id'
            query += f'    order by {order_by} {'desc' if order_direction == 'desc' else ''}'
            query += '''
                offset :offset
                limit :limit
            '''
            
            print(query)
            result = await session.execute(text(query), params)
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
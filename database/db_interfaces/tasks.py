from database.db_interface import BaseInterface
from sqlalchemy import text


class TasksDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
   
    
    async def get_all(self):
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
                tt.check_type
                from tasks_templates tt
                left join fully_completed_tasks fct on fct.task_template_id = tt.id 
                left join started_tasks sct on sct.task_template_id = tt.id;
            '''
            result = await session.execute(text(query))
            return result.mappings().all()
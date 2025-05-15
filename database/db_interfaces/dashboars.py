from dataclasses import field, dataclass
from datetime import date, datetime
from typing import Literal, TypedDict
from xmlrpc.client import DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import user
from database.db_interface import BaseInterface
from sqlalchemy import and_, exists, func, select, text
from database.models import BalanceReasons, TaskTemplate, User, UserBalanceHistory, UserTaskComplete, UsersStatistic
from loguru import logger


class DailyStats(TypedDict):
    users:          dict = {}
    registrations:  dict = {}
    tasks:          dict = {}
    tickets:        dict = {}


@dataclass
class GeneralStats:
    period:         DailyStats
    prev_period:    DailyStats


class DashboardsDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
    
    
    async def get_giveaways_graph(
        self,
        start: datetime | None,
        end: datetime
    ):
        async with self.async_ses() as session:
            query = f'''
            with giveaways_participants_subq as (
            SELECT 
                distinct(g.id) as giveaway_id,
                gp.user_id,
                gp.created_at
            from giveaways g
            join giveaways_participant gp on gp.giveaway_id = g.id
            where gp.created_at <= :end {'and :start <= gp.created_at' if start else ''}
            )
            select g.id, g.name, coalesce(count(gps.giveaway_id), 0) as participants_count
            from giveaways g 
            left join giveaways_participants_subq gps on g.id = gps.giveaway_id
            group by gps.giveaway_id, g.id, g.name
            order by g.id
            '''
            params = {'end': end}
            if start:
                params['start'] = start
            result = await session.execute(text(query), params=params)
            return result.mappings().all()
    
    
    async def get_users_graph(
        self,
        start: datetime,
        end: datetime,
        preset: Literal['ALL', 'NEW', 'REPEATED']
    ):
        match preset:
            case 'ALL':
                query_type = 'all_users'
            case 'NEW':
                query_type = 'new_users'
            case 'REPEATED':
                query_type = 'repeated_users'
                
        async with self.async_ses() as session:
            query = f'''
            WITH dates AS (
                SELECT generate_series(
                    DATE '{start}',
                    DATE '{end}',
                    INTERVAL '1 day'
                )::DATE AS day
            ),
            new_user_ids_subq AS (
                SELECT us.user_id, DATE(us.created_at) AS day
                FROM users_statistic us 
                WHERE type = 'RUN_APP'
                AND us.created_at BETWEEN '{start}' AND '{end}'
                GROUP BY us.user_id, day
            ),
            repeated_users_subq AS (
                SELECT ds.day, tui.user_id
                FROM dates ds
                LEFT JOIN new_user_ids_subq tui ON ds.day = tui.day
                WHERE EXISTS (
                    SELECT 1
                    FROM users_statistic us
                    WHERE us.user_id = tui.user_id
                    AND us.type = 'RUN_APP'
                    AND DATE(us.created_at) < ds.day
                )
            ),
            repeated_users as (
                SELECT ds.day, 
                    COALESCE(COUNT(DISTINCT u.user_id), 0) AS users_count
                FROM dates ds
                LEFT JOIN repeated_users_subq u ON ds.day = u.day
                GROUP BY ds.day
                ORDER BY ds.day
            ),
            new_users as (
                SELECT ds.day, 
                    COALESCE(COUNT(DISTINCT u.user_id), 0) AS users_count
                FROM dates ds
                LEFT JOIN repeated_users_subq u ON ds.day = u.day
                GROUP BY ds.day
                ORDER BY ds.day
            ),
            all_users as (
                SELECT 
                    ds.day,
                    COALESCE(COUNT(DISTINCT tui.user_id), 0) + COALESCE(COUNT(DISTINCT ru.user_id), 0) AS users_count
                FROM dates ds
                LEFT JOIN new_user_ids_subq tui ON ds.day = tui.day
                LEFT JOIN repeated_users_subq ru ON ds.day = ru.day
                GROUP BY ds.day
                ORDER BY ds.day
            )
            select * from {query_type}
            '''
            result = await session.execute(text(query))
        return result.mappings().all()            
    
    
    async def get_wheel_spins_graph(self, start: datetime, end: datetime):
        async with self.async_ses() as session:
            query = f'''
            WITH dates AS (
                SELECT generate_series(
                    DATE '{start}',
                    DATE '{end}',
                    INTERVAL '1 day'
                )::DATE AS day
            ),
            wheel_spins AS (
                SELECT
                    DATE(created_at) AS day,
                    ubh.id wheel_spin_id
                FROM users_balances_history ubh
                WHERE ubh.reason in ('{BalanceReasons.wheel_spin.value}', '{BalanceReasons.wheel_spin_free.value}')
                AND created_at >= '{start}'
                AND created_at <= '{end}'
            )
            SELECT
                d.day,
                COALESCE(count(ws.wheel_spin_id), 0) AS wheel_spins_count
            FROM dates d
            LEFT JOIN wheel_spins ws ON ws.day = d.day
            GROUP BY d.day
            ORDER BY d.day;
            '''     
            
            result = await session.execute(text(query))
        return result.mappings().all()
    
    
    async def get_referals_graph(
        self,
        start: datetime,
        end: datetime
    ):
        async with self.async_ses() as session:
            query = f'''
            WITH dates AS (
                SELECT generate_series(
                    DATE '{start}',
                    DATE '{end}',
                    INTERVAL '1 day'
                )::DATE AS day
            ),
            referals_data AS (
                SELECT
                    DATE(created_at) AS day,
                    u.referrer_id 
                FROM users u
                WHERE u.referrer_id is not null
                AND created_at >= '{start}'
                AND created_at <= '{end}'
            )
            SELECT
                d.day,
                COALESCE(count(r.referrer_id), 0) AS referals_count
            FROM dates d
            LEFT JOIN referals_data r ON r.day = d.day
            GROUP BY d.day
            ORDER BY d.day;
            '''
            result = await session.execute(text(query))
        return result.mappings().all()
    
    
    async def get_graph_tickets(
        self,
        start: datetime,
        end: datetime,
        preset: Literal['IN', 'OUT']
    ):
        async with self.async_ses() as session:
            query = f'''
                WITH dates AS (
                    SELECT generate_series(
                        DATE '{start}',
                        DATE '{end}',
                        INTERVAL '1 day'
                    )::DATE AS day
                ),
                balance_data AS (
                    SELECT
                        DATE(created_at) AS day,
                        type,
                        SUM(amount) AS total
                    FROM users_balances_history
                    WHERE type = '{preset}'
                    AND created_at >= '{start}'
                    AND created_at <= '{end}'
                    GROUP BY day, type
                )
                SELECT
                    d.day,
                    COALESCE(SUM(CASE WHEN b.type = '{preset}' THEN b.total END), 0) AS total
                FROM dates d
                LEFT JOIN balance_data b ON d.day = b.day
                GROUP BY d.day
                ORDER BY d.day;
            '''
            
            result = await session.execute(
                text(query)
            )
            
        return result.mappings().all()

    
    async def get_graph_tasks(self, start: datetime | None, end: datetime):
        async with self.async_ses() as session:
            query = f'''
                with users_completed_tasks AS (
                SELECT
                    utc.task_template_id,
                    utc.user_id, 
                    COUNT(utc.user_id) AS user_completed
                FROM user_tasks_complete utc 
                JOIN tasks_templates tt ON tt.id = utc.task_template_id
                where utc.created_at <= :end {"and utc.created_at >= :start" if start is not None else ''} 
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
                    uct.user_completed>=uct.complete_count 
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
                    uct.user_completed<uct.complete_count 
                group by 
                    uct.task_template_id 
            ),
            tasks as (
                select 
                    uct.task_template_id,
                    count(uct.task_template_id) as started_tasks
                from 
                    tasks_count uct
                group by 
                    uct.task_template_id 
            )
            select
            tt.id,
            tt.title,
            coalesce(fct.fully_completed_tasks, 0) as completed,
            coalesce(sct.started_tasks, 0) as started
            from tasks_templates tt
            left join fully_completed_tasks fct on fct.task_template_id = tt.id 
            left join started_tasks sct on sct.task_template_id = tt.id;
            '''
            
            params = {'end': end}
            if start is not None:
                params['start'] = start 
            result = await session.execute(text(query), params=params)
        return result.mappings().all()
            
    
    async def _get_daily_stats(
        self,
        session: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ):
        ######### Регистрации
        get_registrations_stmt = lambda start_date, end_date: (
            select(
                func.coalesce(func.count(User.id).filter(User.referrer_id.is_(None)), 0).label('registrations_origin'),
                func.coalesce(func.count(User.id).filter(User.referrer_id.is_not(None)), 0).label('registrations_referals')
            )
            .where(User.created_at.between(start_date, end_date))
        ).subquery('r')
            
        registrations_stmt = get_registrations_stmt(start_date, end_date)
        
        ########## Пользователи
        today_user_ids = (
            select(UsersStatistic.user_id)
            .where(
                UsersStatistic.type == "RUN_APP",
                UsersStatistic.created_at.between(start_date, end_date)
            )
            .distinct()
            .subquery()
        )

        repeated_users = (
            select(func.count())
            .select_from(today_user_ids)
            .where(
                exists(
                    select(1)
                    .select_from(UsersStatistic)
                    .where(
                        UsersStatistic.user_id == today_user_ids.c.user_id,
                        UsersStatistic.type == "RUN_APP",
                        UsersStatistic.created_at < start_date
                    )
                )
            )
            .scalar_subquery()
        )

        total_today = (
            select(func.count())
            .select_from(today_user_ids)
            .scalar_subquery()
        )

        new_today = (total_today - repeated_users).label("new_today")

        login_stats_stmt = (
            select(
                total_today.label("users_total"),
                repeated_users.label("users_repeated"),
                new_today.label("users_new")
            )
        ).subquery("login_stats")
        
        ############ Билеты
        tickets_stmt = (
            select(
                func.coalesce(
                    func.sum(UserBalanceHistory.amount)
                    .filter(UserBalanceHistory.type == 'IN')
                    ,
                    0
                ).label("tickets_received"),
                func.coalesce(
                    func.sum(UserBalanceHistory.amount)
                    .filter(UserBalanceHistory.type == 'OUT')
                    ,
                    0
                ).label("tickets_spent")
            )
            .select_from(UserBalanceHistory)
            .where(UserBalanceHistory.created_at.between(start_date, end_date))
        ).subquery("tickets_stmt")


        ############ Задачи

        users_completed_tasks = (
            select(
                UserTaskComplete.task_template_id,
                UserTaskComplete.user_id,
                func.count(UserTaskComplete.user_id).label("user_completed")
            )
            .join(TaskTemplate, TaskTemplate.id == UserTaskComplete.task_template_id)
            .where(UserTaskComplete.created_at.between(start_date, end_date))
            .group_by(UserTaskComplete.task_template_id, UserTaskComplete.user_id)
        ).subquery("users_completed_tasks")

        tasks_count = (
            select(
                users_completed_tasks.c.task_template_id,
                users_completed_tasks.c.user_id,
                users_completed_tasks.c.user_completed,
                TaskTemplate.complete_count
            )
            .join(TaskTemplate, TaskTemplate.id == users_completed_tasks.c.task_template_id)
        ).subquery("tasks_count")

        fully_completed_tasks = (
            select(
                tasks_count.c.task_template_id,
                func.count(tasks_count.c.task_template_id).label("fully_completed_tasks")
            )
            .where(tasks_count.c.user_completed >= tasks_count.c.complete_count)
            .group_by(tasks_count.c.task_template_id)
        ).subquery("fully_completed_tasks")

        started_tasks = (
            select(
                tasks_count.c.task_template_id,
                func.count(tasks_count.c.task_template_id).label("started_tasks")
            )
            .where(tasks_count.c.user_completed < tasks_count.c.complete_count)
            .group_by(tasks_count.c.task_template_id)
        ).subquery("started_tasks")

        task_stats_stmt = (
            select(
                func.sum(func.coalesce(fully_completed_tasks.c.fully_completed_tasks, 0)).label("tasks_completed"),
                func.sum(func.coalesce(started_tasks.c.started_tasks, 0)).label("tasks_started")
            )
            .select_from(TaskTemplate)
            .outerjoin(fully_completed_tasks, fully_completed_tasks.c.task_template_id == TaskTemplate.id)
            .outerjoin(started_tasks, started_tasks.c.task_template_id == TaskTemplate.id)
        ).subquery("task_stats")

        ########## Финальный выбор
        period = await session.execute(
            select(
                tickets_stmt.c.tickets_received.label("tickets_received"),
                tickets_stmt.c.tickets_spent.label("tickets_spent"),
                
                login_stats_stmt.c.users_total.label("users_total"),
                login_stats_stmt.c.users_repeated.label("users_repeated"),
                login_stats_stmt.c.users_new.label("users_new"),
                
                registrations_stmt.c.registrations_referals.label('registrations_referals'),
                registrations_stmt.c.registrations_origin.label('registrations_origin'),
                
                task_stats_stmt.c.tasks_completed.label("tasks_completed"),
                task_stats_stmt.c.tasks_started.label("tasks_started")
            )
            .select_from(registrations_stmt)
        )
        
        db_result = dict(period.mappings().first())
        result = DailyStats(
            registrations={},
            users={},
            tasks={},
            tickets={}
        )
        logger.debug(result)
        for key, value in db_result.items():
            section_key, section_value_key = key.split('_', 1)
            result[section_key][section_value_key] = value            
        return result
    
    
    async def get_general_stats(
        self,
        start_date:   datetime,
        end_date:     datetime,
            
        prev_start_date:  datetime,
        prev_end_date:    datetime,           
    ) -> GeneralStats:
        async with self.async_ses() as session:
            general_stats = GeneralStats(
                period=await self._get_daily_stats(
                    session,
                    start_date,
                    end_date 
                ),
                prev_period=await self._get_daily_stats(
                    session,
                    prev_start_date,
                    prev_end_date 
                )
            ) 
        return general_stats   
    
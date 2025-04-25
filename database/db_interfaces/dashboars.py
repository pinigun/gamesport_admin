from dataclasses import field, dataclass
from datetime import datetime
from typing import TypedDict
from xmlrpc.client import DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import user
from database.db_interface import BaseInterface
from sqlalchemy import and_, exists, func, select, text
from database.models import User, UserBalanceHistory, UsersStatistic
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
        
    
    async def _get_daily_stats(
        self,
        session: AsyncSession,
        start_date: datetime,
        end_date: DateTime
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
                func.sum(UserBalanceHistory.amount)
                    .filter(and_(UserBalanceHistory.type == 'IN'))
                    .label("tickets_received"),
                func.sum(UserBalanceHistory.amount)
                    .filter(and_(UserBalanceHistory.type == 'OUT'))
                    .label("tickets_spent")
            )
            .select_from(UserBalanceHistory)
            .where(UserBalanceHistory.created_at.between(start_date, end_date))
            )
        
        period = await session.execute(
            select(
                tickets_stmt.c.tickets_received.label("tickets_received"),
                tickets_stmt.c.tickets_spent.label("tickets_spent"),
                
                login_stats_stmt.c.users_total.label("users_total"),
                login_stats_stmt.c.users_repeated.label("users_repeated"),
                login_stats_stmt.c.users_new.label("users_new"),
                
                registrations_stmt.c.registrations_referals.label('registrations_referals'),
                registrations_stmt.c.registrations_origin.label('registrations_origin'),
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
            return GeneralStats(
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
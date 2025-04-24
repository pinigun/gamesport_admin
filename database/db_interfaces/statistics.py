import asyncio
from typing import Literal, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from database.models import FAQ, User, UserBalanceHistory, UserSubscription, UsersStatistic, datetime
from sqlalchemy import Date, and_, cast, desc, func, select, text
from database.db_interface import BaseInterface
from loguru import logger

class StatisticsDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
        
    
    async def _get_registrations_stats(self):
        async with self.async_ses() as session:
            result = await session.execute(
                select(
                    func.count(User.id).filter(User.referrer_id.is_(None)).label('origin_users'),
                    func.count(User.id).filter(User.referrer_id.is_not(None)).label('referal_users'),
                )
            )
            
            return result.mappings().one()
    

    # Получаем диапазон всех дат
    def get_date_range(self, start: datetime, end: datetime) -> list[str]:
        current = start.date()
        end_date = end.date()
        dates = []
        while current <= end_date:
            dates.append(current.isoformat())
            current += timedelta(days=1)
        return dates


    # Получаем диапазон всех дат
    def get_date_range(self, start: datetime, end: datetime) -> list[str]:
        current = start.date()
        end_date = end.date()
        dates = []
        while current <= end_date:
            dates.append(current.isoformat())
            current += timedelta(days=1)
        return dates

    async def get_all_stats(
        self,
        min_balance:        Optional[int] = None,
        max_balance:        Optional[int] = None,
        giveway_id:         Optional[int] = None,
        gs_subscription:    Optional[Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']] = None,
        datetime_start:     Optional[datetime] = None,
        datetime_end:       Optional[datetime] = None,
    ):
        async with self.async_ses() as session:
            # Фильтры
            user_filters = []
            balance_filters = []
            logger.debug('Мы тут')
            if datetime_start:
                user_filters.append(User.created_at >= datetime_start)
                balance_filters.append(UserBalanceHistory.created_at >= datetime_start)
            logger.debug('2')
            if datetime_end:
                user_filters.append(User.created_at < datetime_end)
                balance_filters.append(UserBalanceHistory.created_at < datetime_end)
            logger.debug('3')
            if gs_subscription:
                match gs_subscription:
                    case 'FULL':
                        user_filters.append(and_(UserSubscription.lite.is_(True), UserSubscription.pro.is_(True)))
                    case 'LITE':
                        user_filters.append(and_(UserSubscription.lite.is_(True), UserSubscription.pro.is_(False)))
                    case 'PRO':
                        user_filters.append(and_(UserSubscription.lite.is_(False), UserSubscription.pro.is_(True)))
                    case 'UNSUBSCRIBED':
                        user_filters.append(and_(UserSubscription.lite.is_(False), UserSubscription.pro.is_(False)))
            logger.debug('4')
            if giveway_id:
                balance_filters.append(UserBalanceHistory.giveaway_id == giveway_id)

                
            logger.debug('Регистрейшн запрос')
            registrations_stmt = (
                select(
                    cast(User.created_at, Date).label("date"),
                    func.count(User.id).label("users_registrations"),
                    func.count(User.id).filter(User.referrer_id.is_(None)).label("registrations_origin_users"),
                    func.count(User.id).filter(User.referrer_id.is_not(None)).label("registrations_referal_users")
                )
                .select_from(User)
                .outerjoin(UserSubscription, User.id == UserSubscription.user_id)
                .where(*user_filters)
                .group_by(cast(User.created_at, Date))
            ).subquery('r')
            
            logger.debug('Тикетс запрос')
            tickets_stmt = (
                select(
                    cast(UserBalanceHistory.created_at, Date).label("date"),
                    func.sum(UserBalanceHistory.amount)
                        .filter(and_(UserBalanceHistory.type == 'IN'))
                        .label("tickets_received"),
                    func.sum(UserBalanceHistory.amount)
                        .filter(and_(UserBalanceHistory.type == 'OUT'))
                        .label("tickets_spent")
                )
                .select_from(UserBalanceHistory)
                .join(User, User.id == UserBalanceHistory.user_id)
                .outerjoin(UserSubscription, User.id == UserSubscription.user_id)
                .where(*user_filters)
                .where(*balance_filters)
                .group_by(cast(UserBalanceHistory.created_at, Date))
            )
            having_clauses = []
            if min_balance is not None:
                having_clauses.append(
                    func.sum(UserBalanceHistory.amount)
                    .filter(UserBalanceHistory.type == 'IN') >= min_balance
                )
            if max_balance is not None:
                having_clauses.append(
                    func.sum(UserBalanceHistory.amount)
                    .filter(UserBalanceHistory.type == 'IN') <= max_balance
                )

            if having_clauses:
                tickets_stmt = tickets_stmt.having(and_(*having_clauses))
            
            tickets_stmt = tickets_stmt.subquery('t')
            
            # Запрос на статистику пользователей
            user_statistic_statment = (
                select(
                    cast(UsersStatistic.created_at, Date).label("date"),
                    func.count(UsersStatistic.id).filter(UsersStatistic.type == 'RUN_APP').label('users_runs'),
                    func.count(UsersStatistic.id).filter(UsersStatistic.type == 'START_BOT').label('users_starts')
                )
                .group_by(cast(UsersStatistic.created_at, Date))
            ).subquery('us')
            
            
            # Объединяем сабквери, по дате
            logger.debug('Финальный запрос')
            final_stmt = (
                select(
                    func.coalesce(
                        registrations_stmt.c.date,
                        tickets_stmt.c.date
                    ).label("date"),
                    
                    # Пользователи
                    func.coalesce(registrations_stmt.c.users_registrations, 0).label("users_registrations"),
                    func.coalesce(user_statistic_statment.c.users_runs, 0).label('users_runs'),
                    func.coalesce(user_statistic_statment.c.users_starts, 0).label('users_starts'),
                    
                    # Регистрации
                    func.coalesce(registrations_stmt.c.registrations_origin_users, 0).label('registrations_origin_users'),
                    func.coalesce(registrations_stmt.c.registrations_referal_users, 0).label('registrations_referal_users'),
                    
                    # Билеты
                    func.coalesce(tickets_stmt.c.tickets_received, 0).label('tickets_received'),
                    func.coalesce(tickets_stmt.c.tickets_spent, 0).label('tickets_spent')
                    
                )
                .join(tickets_stmt, registrations_stmt.c.date == tickets_stmt.c.date)
                .outerjoin(
                    user_statistic_statment,
                    func.coalesce(
                        registrations_stmt.c.date,
                        tickets_stmt.c.date
                    ) == user_statistic_statment.c.date
                )
                .order_by(desc("date"))
            )
            
            logger.debug('Делаем запрос')
            db_result = await session.execute(final_stmt)
            logger.debug(db_result.mappings())
            result = dict()
            for row in db_result.mappings():
                row = dict(row)
                date = str(row.pop('date'))
                result[date] = {
                    "registrations": {}, 
                    "users": {}, 
                    "tasks": {}, 
                    "tickets": {}, 
                    "giveaways": {}
                }
                for key in row:
                    section_key, section_value_key = key.split('_', 1) 
                    result[date][section_key][section_value_key] = row[key]
            
            return result
                    
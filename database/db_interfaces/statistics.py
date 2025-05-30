import asyncio
from typing import Literal, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import coalesce
from database.models import FAQ, Giveaway, GiveawayEnded, GiveawayParticipant, TaskTemplate, User, UserBalanceHistory, UserSubscription, UserTaskComplete, UserTaskParticipant, UsersStatistic, datetime
from sqlalchemy import Date, and_, asc, cast, desc, distinct, func, select, text
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
        page:               int | None = 1,
        per_page:           int | None = 10,
        min_balance:        Optional[int] = None,
        max_balance:        Optional[int] = None,
        giveaway_id:        Optional[int] = None,
        task_id:            Optional[int] = None,
        gs_subscription:    Optional[Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']] = None,
        datetime_start:     Optional[datetime] = None,
        datetime_end:       Optional[datetime] = None,
        order_by:           Literal['date'] = 'date',
        order_direction:    Literal['desc', 'asc'] = 'desc',
    ):
        async with self.async_ses() as session:
            # Фильтры
            user_filters = []
            balance_filters = []
            giveaways_filters = []
            logger.debug('Мы тут')
            if datetime_start:
                user_filters.append(User.created_at >= datetime_start)
                balance_filters.append(UserBalanceHistory.created_at >= datetime_start)
                giveaways_filters.append(GiveawayParticipant.created_at >= datetime_start)
            logger.debug('2')
            if datetime_end:
                user_filters.append(User.created_at < datetime_end)
                balance_filters.append(UserBalanceHistory.created_at < datetime_end)
                giveaways_filters.append(GiveawayParticipant.created_at <= datetime_end)
            if giveaway_id is not None:
                giveaways_filters.append(GiveawayParticipant.giveaway_id==giveaway_id)
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
            # if giveway_id:
            #     balance_filters.append(UserBalanceHistory.giveaway_id == giveway_id)

                
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
            
            task_filters = []
            if task_id:
                task_filters.append(
                    UserTaskComplete.task_template_id == task_id
                )
            # Статистика по задачам (по дням)
            user_tasks_cte = (
                select(
                    UserTaskComplete.task_template_id,
                    UserTaskComplete.user_id,
                    cast(UserTaskComplete.created_at, Date).label("date"),
                    func.count(UserTaskComplete.id).label("user_completed")
                )
                .where(*task_filters)
                .group_by(UserTaskComplete.task_template_id, UserTaskComplete.user_id, cast(UserTaskComplete.created_at, Date))
            ).cte("user_tasks_cte")

            tasks_count_cte = (
                select(
                    user_tasks_cte.c.user_id,
                    user_tasks_cte.c.task_template_id,
                    user_tasks_cte.c.date,
                    user_tasks_cte.c.user_completed,
                    TaskTemplate.complete_count
                )
                .select_from(user_tasks_cte)
                .join(TaskTemplate, TaskTemplate.id == user_tasks_cte.c.task_template_id)
            ).cte("tasks_count_cte")

            fully_completed_tasks = (
                select(
                    tasks_count_cte.c.date,
                    func.count().label("tasks_completed")
                )
                .where(tasks_count_cte.c.user_completed >= tasks_count_cte.c.complete_count)
                .group_by(tasks_count_cte.c.date)
            ).cte("fully_completed_tasks")

            started_tasks = (
                select(
                    tasks_count_cte.c.date,
                    func.count().label("tasks_started_partial")
                )
                .where(tasks_count_cte.c.user_completed < tasks_count_cte.c.complete_count)
                .group_by(tasks_count_cte.c.date)
            ).cte("started_tasks")

            # opened = назначено, но не начато (нет записей в user_tasks_complete)
            utp = aliased(UserTaskParticipant)
            utc = aliased(UserTaskComplete)

            opened_tasks = (
                select(
                    cast(utp.created_at, Date).label("date"),
                    func.count().label("tasks_opened")
                )
                .select_from(utp)
                .outerjoin(
                    utc,
                    and_(
                        utp.task_template_id == utc.task_template_id,
                        utp.user_id == utc.user_id
                    )
                )
                .where(utc.task_template_id.is_(None))
                .group_by(cast(utp.created_at, Date))
            ).cte("opened_tasks")

            tasks_stmt = (
                select(
                    coalesce(fully_completed_tasks.c.date, started_tasks.c.date, opened_tasks.c.date).label("date"),
                    coalesce(fully_completed_tasks.c.tasks_completed, 0).label("tasks_completed"),
                    (coalesce(started_tasks.c.tasks_started_partial, 0) + coalesce(opened_tasks.c.tasks_opened, 0)).label("tasks_started")
                )
                .outerjoin(started_tasks, fully_completed_tasks.c.date == started_tasks.c.date)
                .outerjoin(opened_tasks, fully_completed_tasks.c.date == opened_tasks.c.date)
            ).subquery("tasks_stmt")

            # Prepare subquery for giveaway participants in the specified time range
            giveaways_participants_subq = (
                select(
                    Giveaway.id.label('giveaway_id'),
                    GiveawayParticipant.user_id,
                    GiveawayParticipant.created_at
                )
                .join(GiveawayParticipant, GiveawayParticipant.giveaway_id == Giveaway.id)
                .where(and_(*giveaways_filters))  # Applying filters for participants
                .distinct()
                .subquery()
            )

            # Subquery for previous participants before the datetime_start if provided
            previous_participants_subq = (
                select(
                    Giveaway.id.label('giveaway_id'),
                    GiveawayParticipant.user_id
                )
                .join(GiveawayParticipant, GiveawayParticipant.giveaway_id == Giveaway.id)
                .where(GiveawayParticipant.created_at < datetime_start if datetime_start else True)  # If no datetime_start, get all records
                .distinct()
                .subquery()
            )

            # Query for giveaways statistics (primary and repeated participants)
            giveaways_stats = (
                select(
                    cast(giveaways_participants_subq.c.created_at, Date).label("date"),
                    func.count(distinct(giveaways_participants_subq.c.user_id)).label("giveaways_primary"),
                    func.count(distinct(previous_participants_subq.c.user_id)).label("giveaways_repeated")
                )
                .outerjoin(previous_participants_subq, giveaways_participants_subq.c.giveaway_id == previous_participants_subq.c.giveaway_id)
                .group_by(cast(giveaways_participants_subq.c.created_at, Date))
            ).subquery("giveaways_stats")
            
            # Назначаем order_by
            match order_by:
                case _:
                    order_by="date"
            
            # Объединяем сабквери в финальном запросе
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
                    func.coalesce(tickets_stmt.c.tickets_spent, 0).label('tickets_spent'),

                    # Задачи
                    func.coalesce(tasks_stmt.c.tasks_started, 0).label("tasks_started"),
                    func.coalesce(tasks_stmt.c.tasks_completed, 0).label("tasks_completed"),

                    # Розыгрыши
                    func.coalesce(giveaways_stats.c.giveaways_primary, 0).label("giveaways_primary"),
                    func.coalesce(giveaways_stats.c.giveaways_repeated, 0).label("giveaways_repeated")
                )
                .join(tickets_stmt, registrations_stmt.c.date == tickets_stmt.c.date)
                .outerjoin(
                    user_statistic_statment,
                    func.coalesce(
                        registrations_stmt.c.date,
                        tickets_stmt.c.date
                    ) == user_statistic_statment.c.date
                )
                .outerjoin(tasks_stmt, tasks_stmt.c.date == func.coalesce(registrations_stmt.c.date, tickets_stmt.c.date))
                .outerjoin(giveaways_stats, giveaways_stats.c.date == func.coalesce(registrations_stmt.c.date, tickets_stmt.c.date))
                .order_by(desc(order_by) if order_direction == 'desc' else asc(order_by))

            )
            
            logger.debug('Делаем запрос')
            db_result = await session.execute(final_stmt.offset((page-1)*per_page).limit(per_page))
            total_items = await session.scalar(select(func.count()).select_from(final_stmt))
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

            return result, total_items
                    

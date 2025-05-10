import asyncio
from datetime import datetime
import hashlib
from typing import Literal, TypedDict
from sqlalchemy import and_, case, desc, distinct, exists, func, or_, select, text, update
from sqlalchemy.orm import aliased
from database.db_interface import BaseInterface
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.models import GiveawayParticipant, TaskTemplate, User, UserBalanceHistory, UserSubscription, UserTaskComplete


class UserData(TypedDict):
    id:                 int
    created_at:         str | datetime
    tg_id:              str | None
    vk_id:              str | None
    email:              str | None
    balance:            float
    giveaways_count:    int
    gs_subscription:    Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']
    referals_count:     int = 0
    
    # Unsupported  
    gs_id:              int | None = None
    completed_tasks:    int | None = None 
    deleted:            bool

class UsersDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)

    
    async def get_filtered_count(
        self,
        created_at_start: datetime = None,
        created_at_end: datetime = None,
        min_balance: int | None = None,
        max_balance: int | None = None,
        giveway_id: int | None = None,
        gs_subscription: Literal["FULL", "LITE", "PRO", "UNSUBSCRIBED"] | None = None,
        **another_filters
    ) -> int:
        async with self.async_ses() as session:
            balance_case = func.sum(
                case(
                    (UserBalanceHistory.type == "IN", UserBalanceHistory.amount),
                    else_=-UserBalanceHistory.amount
                )
            ).label("balance")

            query = (
                select(User.id)
                .outerjoin(UserBalanceHistory, User.id == UserBalanceHistory.user_id)
                .outerjoin(UserSubscription, User.id == UserSubscription.user_id)
                .outerjoin(
                    GiveawayParticipant,
                    User.id == GiveawayParticipant.user_id
                )
                .group_by(User.id, UserSubscription.lite, UserSubscription.pro)
            )

            # Фильтр по дате
            if created_at_start:
                query = query.where(User.created_at >= created_at_start)
            if created_at_end:
                query = query.where(User.created_at <= created_at_end)

            # Фильтр по подписке
            if gs_subscription is not None:
                match gs_subscription:
                    case "FULL":
                        query = query.where(
                            and_(
                                UserSubscription.lite == True,
                                UserSubscription.pro == True
                            )
                        )
                    case "LITE":
                        query = query.where(
                            and_(
                                UserSubscription.lite == True,
                                UserSubscription.pro == False
                            )
                        )
                    case "PRO":
                        query = query.where(
                            and_(
                                UserSubscription.lite == False,
                                UserSubscription.pro == True
                            )
                        )
                    case "UNSUBSCRIBED":
                        query = query.where(
                            (UserSubscription.lite != True) & (UserSubscription.pro != True) |
                            (UserSubscription.lite.is_(None) & UserSubscription.pro.is_(None))
                        )

            # Фильтры по балансу
            if min_balance is not None or max_balance is not None:
                having_conditions = []
                if min_balance is not None:
                    having_conditions.append(balance_case >= min_balance)
                if max_balance is not None:
                    having_conditions.append(balance_case <= max_balance)
                query = query.having(and_(*having_conditions))

            # Фильтр по giveaway_id
            if giveway_id is not None:
                query = query.where(GiveawayParticipant.giveaway_id == giveway_id)

            # Фильтры по другим полям
            if another_filters:
                for key, value in another_filters.items():
                    attr = getattr(User, key, None)
                    if attr is not None:
                        query = query.where(attr == value)

            count_query = select(func.count()).select_from(query.subquery())
            result = await session.scalar(count_query)
            return result if result else 0


     
    async def _get_user_balance(self, session: AsyncSession, user_id: int) -> int:
        balance = 0
        user_balance_history = await session.execute(
            select(UserBalanceHistory)
            .where(UserBalanceHistory.user_id == user_id)
        )
        user_balance_history = user_balance_history.scalars().all()
        
        for record in user_balance_history:
            if record.type.upper() == 'IN':
                balance += record.amount
            else:
                balance -= record.amount
        
        return balance
    
    
    async def _get_giweaways_count(self, session: AsyncSession, user_id: int) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(GiveawayParticipant)
                .where(GiveawayParticipant.user_id == user_id)
            )
        )
        
        
    async def _get_gs_subscription(self, session: AsyncSession, user_id: int) -> Literal['ALL', 'PRO', 'LITE'] | None:
        gs_subscriptions = await session.execute(
            select(UserSubscription.lite, UserSubscription.pro)
            .where(UserSubscription.user_id == user_id)
        )
        gs_subscriptions = gs_subscriptions.one_or_none()        
        if gs_subscriptions is None:
            return "UNSUBSCRIBED"
        
        if all(gs_subscriptions):
            return 'FULL'
        elif gs_subscriptions[0] == True:
            return 'LITE'
        elif gs_subscriptions[1] == True:
            return 'PRO'
        else:
            return "UNSUBSCRIBED"


    def _map_subs(self, lite: bool | None, pro: bool | None) -> str:
        if lite and pro:
            return "FULL"
        elif lite:
            return "LITE"
        elif pro:
            return "PRO"
        return "UNSUBSCRIBED"
    
    
    async def update_user(self, user_id: int, user_data: dict):
        async with self.async_ses() as session:
            current_balance = await session.scalar(text("""
                SELECT 
                    COALESCE(SUM(
                        CASE 
                            WHEN type = 'IN' THEN amount
                            ELSE -amount
                        END
                    ), 0) AS balance
                FROM users_balances_history
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            logger.debug(current_balance)          
            balance_transaction_amount = user_data.pop('balance', None)  
            if balance_transaction_amount:
                if balance_transaction_amount + current_balance >= 0:
                    amount = balance_transaction_amount if balance_transaction_amount > 0 else -balance_transaction_amount
                    transaction_type = 'IN' if balance_transaction_amount > 0 else 'OUT'
                else:
                    amount = current_balance
                    transaction_type = 'OUT'
                new_history_record=UserBalanceHistory(
                    user_id=user_id,
                    type=transaction_type,
                    reason='Changed by administrator',
                    amount=amount,
                    created_at=datetime.now()
                )
                logger.debug(new_history_record.__dict__)
                session.add(new_history_record)
            password = user_data.pop('password', None)
            if password:
                user_data['hashed_password'] = hashlib.md5(password.encode()).hexdigest()
              
                
            if user_data:  
                row = await session.execute(
                    update(User)
                    .filter_by(id=user_id)
                    .values(**user_data)
                    .returning(User)
                )
                await session.refresh(row.scalar())
            
            await session.commit()
         
            
        return (await self.get_all(page=1, per_page=1, id=user_id))[0]
    
    
    async def get_all(
        self,
        page:               int,
        per_page:           int,
        order_by:           str = 'user_id',
        order_direction:    Literal['asc', 'desc'] = 'asc',
        created_at_start:   datetime = None,
        created_at_end:     datetime = None,
        min_balance:        int | None = None,
        max_balance:        int | None = None,
        giveway_id:         int | None = None,
        task_id:            int | None = None,
        gs_subscription:    Literal["FULL", "LITE", "PRO", "UNSUBSCRIBED"] | None = None,
        **another_filters
    ) -> list[UserData]:
        async with self.async_ses() as session:
            balance_subq = (
                select(
                    UserBalanceHistory.user_id,
                    func.sum(
                        case(
                            (UserBalanceHistory.type == "IN", UserBalanceHistory.amount),
                            else_=-UserBalanceHistory.amount
                        )
                    ).label("balance")
                )
                .group_by(UserBalanceHistory.user_id)
                .subquery()
            )

            giveaways_count = func.count(distinct(GiveawayParticipant.id)).label("giveaways_count")
            UserAlias = aliased(User)
            referals_count_subquery = (
                select(
                    UserAlias.referrer_id,
                    func.count(UserAlias.id).label("referals_count")
                )
                .group_by(UserAlias.referrer_id)
                .alias("referals_count_subquery")
            )

            # Подсчёт фактических выполнений задач пользователем
            user_task_completions_subq = (
                select(
                    UserTaskComplete.task_template_id,
                    UserTaskComplete.user_id,
                    func.count(UserTaskComplete.user_id).label('user_completed_count')
                )
                .join(TaskTemplate, TaskTemplate.id == UserTaskComplete.task_template_id)
                .group_by(UserTaskComplete.task_template_id, UserTaskComplete.user_id)
            )
            
            # if task_id
            
            # Дополняем данными о требуемых выполнениях
            user_task_completion_with_requirements_subq = (
                select(
                    user_task_completions_subq.c.user_id,
                    user_task_completions_subq.c.task_template_id,
                    user_task_completions_subq.c.user_completed_count,
                    TaskTemplate.complete_count
                )
                .join(TaskTemplate, TaskTemplate.id == user_task_completions_subq.c.task_template_id)
                .subquery()
            )

            # Считаем, сколько тасок реально закрыто полностью у каждого пользователя
            fully_completed_tasks_by_user_subq = (
                select(
                    user_task_completion_with_requirements_subq.c.user_id.label('user_id'),
                    func.count(user_task_completion_with_requirements_subq.c.user_id).label('completed_tasks')
                )
                .where(
                    user_task_completion_with_requirements_subq.c.user_completed_count == user_task_completion_with_requirements_subq.c.complete_count
                )
                .group_by(user_task_completion_with_requirements_subq.c.user_id)
                .subquery()
            )

            query = (
                select(
                    User.id,
                    User.gs_id,
                    User.created_at,
                    User.tg_id,
                    User.username,
                    User.vk_id,
                    User.email,
                    User.deleted,
                    giveaways_count,
                    func.coalesce(balance_subq.c.balance, 0).label("balance"),
                    func.coalesce(fully_completed_tasks_by_user_subq.c.completed_tasks, 0).label('completed_tasks'),
                    func.coalesce(referals_count_subquery.c.referals_count, 0).label('referals_count'),
                    UserSubscription.lite,
                    UserSubscription.pro
                )
                .outerjoin(UserBalanceHistory, User.id == UserBalanceHistory.user_id)
                .outerjoin(UserSubscription, User.id == UserSubscription.user_id)
                .outerjoin(GiveawayParticipant, User.id == GiveawayParticipant.user_id)
                .outerjoin(
                    referals_count_subquery,  # Явное соединение с подзапросом referals_count_subquery
                    referals_count_subquery.c.referrer_id == User.id
                )
                .outerjoin(
                    fully_completed_tasks_by_user_subq,  # Явное соединение с подзапросом referals_count_subquery
                    fully_completed_tasks_by_user_subq.c.user_id == User.id
                )
                .outerjoin(balance_subq, balance_subq.c.user_id == User.id)
                .group_by(
                    User.id, 
                    User.created_at,
                    User.tg_id,
                    User.username,
                    User.vk_id,
                    User.email,
                    User.deleted,
                    UserSubscription.lite,
                    UserSubscription.pro,
                    balance_subq.c.balance,
                    referals_count_subquery.c.referals_count,
                    fully_completed_tasks_by_user_subq.c.completed_tasks
                )
            )

            # created_at фильтр
            if created_at_start:
                query = query.where(User.created_at >= created_at_start)
            if created_at_end:
                query = query.where(User.created_at <= created_at_end)

            # balance фильтры
            if min_balance is not None or max_balance is not None:
                having_conditions = []
                if min_balance is not None:
                    having_conditions.append(balance_subq.c.balance >= min_balance)
                if max_balance is not None:
                    having_conditions.append(balance_subq.c.balance <= max_balance)
                query = query.having(and_(*having_conditions))

            # подписка фильтр
            if gs_subscription is not None:
                match gs_subscription:
                    case "FULL":
                        query = query.where(
                            and_(
                                UserSubscription.lite == True, 
                                UserSubscription.pro == True
                            )
                        )
                    case "LITE":
                        query = query.where(
                            and_(
                                UserSubscription.lite == True, 
                                UserSubscription.pro == False
                            )
                        )
                    case "PRO":
                        query = query.where(
                            and_(
                                UserSubscription.lite == False, 
                                UserSubscription.pro == True
                            )
                        )
                    case "UNSUBSCRIBED":
                        query = query.where(
                            (UserSubscription.lite != True) & (UserSubscription.pro != True) |
                            (UserSubscription.lite.is_(None) & UserSubscription.pro.is_(None))
                        )

            if giveway_id is not None:
                subq = (
                    select(1)
                    .select_from(GiveawayParticipant)
                    .where(
                        and_(
                            GiveawayParticipant.user_id == User.id,
                            GiveawayParticipant.giveaway_id == giveway_id
                        )
                    )
                    .correlate(User)
                )

                query = query.where(exists(subq))

            if another_filters:
                for key, value in another_filters.items():
                    attr = getattr(User, key, None)
                    if attr is not None:
                        if key == 'tg_id':
                            query = query.where(or_(User.tg_id == value, User.username == value))
                        else:
                            query = query.where(attr == value)    

            if order_by == 'user_id':
                order_by_param = User.id
            else:
                order_by_param = User.created_at
            result = await session.execute(
                query
                .offset((page - 1) * per_page)
                .limit(per_page)
                .order_by(order_by_param.desc() if order_direction == 'desc' else order_by_param.asc())
            )

            rows = result.all()
            return [
                UserData(
                    id=row.id,
                    gs_id=row.gs_id,
                    created_at=row.created_at,
                    tg_id=row.tg_id,
                    username=row.username,
                    vk_id=row.vk_id,
                    email=row.email,
                    balance=row.balance,
                    giveaways_count=row.giveaways_count,
                    referals_count=row.referals_count,
                    completed_tasks=row.completed_tasks, 
                    gs_subscription=self._map_subs(row.lite, row.pro),
                    deleted=row.deleted
                )
                for row in rows
            ]
            
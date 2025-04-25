import asyncio
from datetime import datetime
import hashlib
from typing import Literal, TypedDict
from sqlalchemy import and_, case, desc, distinct, exists, func, select, update
from sqlalchemy.orm import aliased
from database.db_interface import BaseInterface
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.models import GiveawayParticipant, User, UserBalanceHistory, UserSubscription


class UserData(TypedDict):
    id:                 int
    created_at:         str | datetime
    tg_id:              str | None
    phone:              str | None
    email:              str | None
    balance:            float
    giveaways_count:    int
    gs_subscription:    Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']
    referals_count:     int = 0
    
    # Unsupported  
    gs_id:              int | None = None
    completed_tasks:    int | None = None 
    

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
            balance_case = func.sum(
                case(
                    (UserBalanceHistory.type == "IN", UserBalanceHistory.amount),
                    else_=-UserBalanceHistory.amount
                )
            ).label("balance")
            balance_transaction_amount = user_data.pop('balance', None)            
            if balance_transaction_amount:
                new_history_record=UserBalanceHistory(
                    user_id=user_id,
                    type='IN' if balance_transaction_amount > 0 else 'OUT',
                    reason='Changed by administrator',
                    amount=balance_transaction_amount if balance_transaction_amount > 0 else -balance_transaction_amount,
                    created_at=datetime.now()
                )
                session.add(new_history_record)
            password = user_data.pop('password', None)
            if password:
                user_data['hashed_password'] = hashlib.md5(password.encode()).hexdigest()
            password = user_data.pop('password', None)
            if password:
                user_data['hashed_password'] = hashlib.md5(password.encode()).hexdigest()
                
            row = await session.execute(
                update(User)
                .filter_by(id=user_id)
                .values(**user_data)
                .returning(User)
            )
            await session.commit()
            await session.refresh(row.scalar())
            
            giveaways_count = func.count(distinct(GiveawayParticipant.id)).label("giveaways_count")
            query = (
                select(
                    User.id,
                    User.created_at,
                    User.tg_id,
                    User.phone,
                    User.email,
                    balance_case,
                    giveaways_count,
                    UserSubscription.lite,
                    UserSubscription.pro
                )
                .outerjoin(UserBalanceHistory, User.id == UserBalanceHistory.user_id)
                .outerjoin(UserSubscription, User.id == UserSubscription.user_id)
                .outerjoin(
                    GiveawayParticipant, 
                    User.id == GiveawayParticipant.user_id,
                )
                .group_by(User.id, User.created_at, User.tg_id, User.phone, User.email,
                        UserSubscription.lite, UserSubscription.pro)
            )
            result = await session.execute(
                query
                .where(User.id==user_id)
                .order_by(User.id)
            )
            row = result.one()
            return UserData(
                id=row.id,
                created_at=row.created_at,
                tg_id=row.tg_id,
                phone=row.phone,
                email=row.email,
                balance=row.balance,
                giveaways_count=row.giveaways_count,
                gs_subscription=self._map_subs(row.lite, row.pro),
            )
    
    
    async def get_all(
        self,
        page: int,
        per_page: int,
        created_at_start: datetime = None,
        created_at_end: datetime = None,
        min_balance: int | None = None,
        max_balance: int | None = None,
        giveway_id: int | None = None,
        gs_subscription: Literal["FULL", "LITE", "PRO", "UNSUBSCRIBED"] | None = None,
        **another_filters
    ) -> list[UserData]:
        async with self.async_ses() as session:
            balance_case = func.sum(
                case(
                    (UserBalanceHistory.type == "IN", UserBalanceHistory.amount),
                    else_=-UserBalanceHistory.amount
                )
            ).label("balance")

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
            
            query = (
                select(
                    User.id,
                    User.created_at,
                    User.tg_id,
                    User.phone,
                    User.email,
                    balance_case,
                    giveaways_count,
                    func.coalesce(referals_count_subquery.c.referals_count, 0).label('referals_count'),
                    UserSubscription.lite,
                    UserSubscription.pro
                )
                .outerjoin(UserBalanceHistory, User.id == UserBalanceHistory.user_id)
                .outerjoin(UserSubscription, User.id == UserSubscription.user_id)
                .outerjoin(
                    GiveawayParticipant, 
                    User.id == GiveawayParticipant.user_id,
                )
                .outerjoin(referals_count_subquery, referals_count_subquery.c.referrer_id == User.id)
                .group_by(
                    User.id, 
                    User.created_at,
                    User.tg_id,
                    User.phone,
                    User.email,
                    UserSubscription.lite,
                    UserSubscription.pro,
                    referals_count_subquery.c.referals_count
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
                    having_conditions.append(balance_case >= min_balance)
                if max_balance is not None:
                    having_conditions.append(balance_case <= max_balance)
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
                    .correlate(User)  # ⬅️ ВАЖНО!
                )

                query = query.where(exists(subq))
            
            if another_filters:
                for key, value in another_filters.items():
                    attr = getattr(User, key, None)
                    if attr is not None:
                        query = query.where(attr == value)    
            
            result = await session.execute(
                query
                .offset((page - 1) * per_page)
                .limit(per_page)
                .order_by(User.created_at.desc())
            )
            rows = result.all()
            return [
                UserData(
                    id=row.id,
                    created_at=row.created_at,
                    tg_id=row.tg_id,
                    phone=row.phone,
                    email=row.email,
                    balance=row.balance,
                    giveaways_count=row.giveaways_count,
                    referals_count=row.referals_count,
                    gs_subscription=self._map_subs(row.lite, row.pro),
                )
                for row in rows
            ]
    
    async def __get_full_user_data(self, session: AsyncSession, user: User):
        return UserData(
            id=user.id,
            created_at=user.created_at,
            tg_id=user.tg_id,
            phone=user.phone,
            email=user.email,
            balance=await self._get_user_balance(session, user.id),
            giveaways_count=await self._get_giweaways_count(session, user.id),
            gs_subscription=await self._get_gs_subscription(session, user.id)
        )
     
            
    # async def get_all(
    #     self,
    #     page: int,
    #     per_page: int,
    #     created_at_range: tuple[datetime, datetime] = None,
    #     **filters,
    # ) -> list[UserData]:
    #     async with self.async_ses() as session:
    #         query = (
    #             select(User)
    #             .offset((page-1) * per_page)
    #             .limit(per_page)
    #             .order_by(desc(User.id))
    #         )
            
            
    #         users = await session.execute(query)
    #         users = users.scalars().all()
            
    #         return await asyncio.gather(
    #             *[
    #                 self.get_full_user_data(session, user)
    #                 for user in users
    #             ]
    #         )
            
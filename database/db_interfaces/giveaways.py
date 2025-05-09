from datetime import datetime
from typing import TypedDict

from loguru import logger
from sqlalchemy.testing.suite import DateTest
from database.db_interface import BaseInterface
from database.exceptions import FAQNotFound
from database.models import FAQ, Giveaway, GiveawayEnded, GiveawayParticipant, GiveawayPrize
from sqlalchemy import and_, select, text, update


class GiveawaysDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
    
    
    async def delete_prize(self, prize_id: int):
        await self.delete_rows(
            GiveawayPrize,
            id=prize_id
        )
    
    
    async def add_prizes(self, giveaway_id: int, prizes_data: list[dict]):
        return await self.add_rows(
            models=[
                GiveawayPrize(
                    giveaway_id=giveaway_id,
                    **prize_data
                )
                for prize_data in prizes_data
            ]
        )
    
    
    async def add_winner(
        self,
        giveaway_id: int,
        winner_id: int,
        prize_id: int
    ) -> None:
        await self.add_row(
            GiveawayEnded,
            giveaway_id=giveaway_id,
            winner_id=winner_id,
            prize_id=prize_id,
            end_date=datetime.now()
        )
        
        
    async def get_participtants(
        self,
        page: int,
        per_page: int,
        giveaway_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        async with self.async_ses() as session:
            query = f'''
                select distinct on (gp.user_id)
                    gp.user_id as id,
                    u.email,
                    u.phone,
                    u.tg_id,
                    u.vk_id,
                    ge.prize_id,
                    gpz.name as prize_name
                from giveaways_participant gp 
                left join users u on u.id = gp.user_id
                left join giveaways_ended ge on ge.giveaway_id = gp.giveaway_id and ge.winner_id = gp.user_id
                left join giveaways_prizes gpz on gpz.id = ge.prize_id
                where gp.giveaway_id = :giveaway_id 
                    {"and :start_date <= gp.created_at" if start_date else ''} {"and gp.created_at <= :end_date" if end_date else ''}
                offset :offset
                limit :limit
            '''
            params = {
                'giveaway_id': giveaway_id,
                'offset': (page-1)*per_page,
                'limit': per_page
            }
            if end_date:
                params['end_date'] = end_date
            if start_date:
                params['start_date'] = start_date
            result = await session.execute(text(query), params=params)
        return result.mappings().all()
    
    
    async def get_giveaways_count(self):
        return await self.get_rows_count(Giveaway)
    
    
    async def get_history_count(self):
        async with self.async_ses() as session:
            query = '''
                with giveaways_participants_count as (
                    select giveaway_id, count(*) as participants_count
                    from giveaways_participant
                    group by giveaway_id
                ),
                previous_end_date as (
                    select
                        ge1.giveaway_id,
                        ge1.end_date as start_end_date,
                        (
                            select max(ge2.end_date)
                            from giveaways_ended ge2
                            where ge2.giveaway_id = ge1.giveaway_id
                            and ge2.end_date < ge1.end_date
                        ) as previous_end_date
                    from giveaways_ended ge1
                )
                select count(*) from (select
                    coalesce(
                        case
                            when g.start_date > ge.end_date then
                                (
                                    select max(ge2.end_date)
                                    from giveaways_ended ge2
                                    where ge2.giveaway_id = g.id
                                    and ge2.end_date < ge.end_date
                                )
                            else g.start_date
                        end,
                        null
                    ) as start_date,
                    ge.end_date,
                    g.id as number,
                    coalesce(participants.participants_count, 0) as participants_count,
                    g.price,
                    (coalesce(participants.participants_count, 0) * g.price) as spent_tickets,
                    json_agg(
                        json_build_object(
                            'id', ge.winner_id,
                            'email', u.email,
                            'tg_id', u.tg_id,
                            'phone', u.phone,
                            'prize_id', ge.giveaway_id,
                            'prize_name', gp.name
                        )
                    ) FILTER (WHERE ge.winner_id IS NOT NULL) as winners
                from giveaways g
                left join giveaways_participants_count participants on participants.giveaway_id = g.id
                left join giveaways_ended ge on g.id = ge.giveaway_id
                left join users u on ge.winner_id = u.id
                left join giveaways_prizes gp on gp.id = ge.prize_id
                group by g.start_date, g.id, ge.end_date, participants.participants_count, g.price
                ) as subq
            '''
            return await session.scalar(text(query))
            
    
    async def get_participants_count(
        self,
        giveaway_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ):
        filters = []
        if start_date:
            filters.append(start_date <= GiveawayParticipant.created_at)
        if end_date:
            filters.append(GiveawayParticipant.created_at <= end_date)
        return await self.get_rows_count(
            GiveawayParticipant,
            filters=filters,
            giveaway_id=giveaway_id
        )
    
    
    async def get_prizes_count(self, giveaway_id: int):
        return await self.get_rows_count(GiveawayPrize, giveaway_id=giveaway_id)
    
    
    async def get_history(self, page: int, per_page: int):
        async with self.async_ses() as session:
            result = await session.execute(
                text('''
                with giveaways_participants_count as (
                    select giveaway_id, count(*) as participants_count
                    from giveaways_participant
                    group by giveaway_id
                ),
                previous_end_date as (
                    select
                        ge1.giveaway_id,
                        ge1.end_date as start_end_date,
                        (
                            select max(ge2.end_date)
                            from giveaways_ended ge2
                            where ge2.giveaway_id = ge1.giveaway_id
                            and ge2.end_date < ge1.end_date
                        ) as previous_end_date
                    from giveaways_ended ge1
                )
                select
                    g.id,
                    coalesce(
                        case
                            when g.start_date > ge.end_date then
                                (
                                    select max(ge2.end_date)
                                    from giveaways_ended ge2
                                    where ge2.giveaway_id = g.id
                                    and ge2.end_date < ge.end_date
                                )
                            else g.start_date
                        end,
                        null
                    ) as start_date,
                    ge.end_date,
                    g.id as number,
                    coalesce(participants.participants_count, 0) as participants_count,
                    g.price,
                    (coalesce(participants.participants_count, 0) * g.price) as spent_tickets,
                    json_agg(
                        json_build_object(
                            'id', ge.winner_id,
                            'email', u.email,
                            'tg_id', u.tg_id,
                            'vk_id', u.vk_id,
                            'phone', u.phone,
                            'prize_id', ge.giveaway_id,
                            'prize_name', gp.name
                        )
                    ) FILTER (WHERE ge.winner_id IS NOT NULL) as winners
                from giveaways g
                left join giveaways_participants_count participants on participants.giveaway_id = g.id
                left join giveaways_ended ge on g.id = ge.giveaway_id
                left join users u on ge.winner_id = u.id
                left join giveaways_prizes gp on gp.id = ge.prize_id
                group by g.start_date, g.id, ge.end_date, participants.participants_count, g.price
                offset :offset
                limit :limit
                     '''
                ),
                {
                    'offset': (page - 1) * per_page,
                    'limit': per_page
                }
            )
            return result.mappings().all()
    
    
    async def add(self, **new_giveaway_data) -> Giveaway:
        return await self.add_row(
            Giveaway,
            **new_giveaway_data
        )
        
        
    async def update(self, giveaway_id: int, **new_data) -> Giveaway:
        return await self.update_rows(
            Giveaway,
            filter_by={'id': giveaway_id},
            **new_data
        )
        
        
    async def update_prize(self, prize_id: int, giveaway_id: int, **new_data) -> Giveaway:
        return await self.update_rows(
            GiveawayPrize,
            filter_by={'giveaway_id': giveaway_id, "id": prize_id},
            **new_data
        )
    

    async def get_all(
        self,
        page: int = 1,
        per_page: int = 10,
        giveaway_id: int | None = None,
        order_by: str | None = None,
        order_direction: str | None = None
    ):
        async with self.async_ses() as session:
            # Формируем базовый запрос
            query = '''
                    WITH giveaways_participants_count AS (
                        SELECT giveaway_id, COUNT(*) AS participants_count
                        FROM giveaways_participant
                        GROUP BY giveaway_id
                    ),
                    last_winners AS (
                        SELECT DISTINCT ON (ge.giveaway_id)
                            ge.giveaway_id,
                            ge.winner_id
                        FROM giveaways_ended ge
                        ORDER BY ge.giveaway_id, ge.end_date DESC
                    )
                    SELECT 
                        g.id, 
                        g.start_date,
                        g.id AS number,
                        g.period_days,
                        g.name,
                        g.price,
                        g.active,
                        lw.winner_id,
                        COALESCE(participants.participants_count, 0) AS participants_count,
                        (COALESCE(participants.participants_count, 0) * g.price) AS spent_tickets,
                        g.photo
                    FROM giveaways g
                    LEFT JOIN giveaways_participants_count participants ON participants.giveaway_id = g.id
                    LEFT JOIN last_winners lw ON lw.giveaway_id = g.id
                    '''

            # Добавляем условие по giveaway_id, если он указан
            if giveaway_id is not None:
                query += " WHERE g.id = :giveaway_id"
            
            if order_by == 'id':
                order_by = 'g.id'
            elif order_by == 'start_date':
                order_by = 'g.start_date'
            elif order_by == 'active':
                order_by = 'g.active'
            logger.debug(order_by)
            query += f'''
                ORDER BY {order_by} {order_direction if order_direction == 'desc' else ''}
                LIMIT :limit
                OFFSET :offset
            '''

            # Параметры запроса
            params = {
                "limit": per_page,
                "offset": (page - 1) * per_page,
            }

            # Если giveaway_id указан, добавляем его в параметры
            if giveaway_id is not None:
                params["giveaway_id"] = giveaway_id

            # Выполняем запрос
            result = await session.execute(text(query), params)

            # Если giveaway_id указан, возвращаем только один элемент
            if giveaway_id:
                result = dict(result.mappings().first())  
                # Запрашиваем призы для конкретного конкурса
                result["prizes"] = [dict(row) for row in (await session.execute(
                    text(
                        '''
                        SELECT id, name, position, photo FROM giveaways_prizes g
                        WHERE g.giveaway_id = :giveaway_id
                        ORDER BY g.position
                        '''
                    ),
                    {
                        "giveaway_id": giveaway_id
                    }
                )
                ).mappings().all()]
                return result
            
            # Если giveaway_id не указан, возвращаем все конкурсы
            return [dict(row) for row in result.mappings().all()]
        
        
    async def get_prizes(self, giveaway_id: int, page: int, per_page: int):
        return await self.get_rows(
            GiveawayPrize,
            giveaway_id=giveaway_id,
            offset=(page-1)*per_page,
            limit=per_page,
            order_by='position'
        )
        
        
    

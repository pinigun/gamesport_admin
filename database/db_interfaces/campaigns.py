from datetime import datetime, timedelta
from loguru import logger
import sqlalchemy
from sqlalchemy.dialects.postgresql import asyncpg
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_interface import BaseInterface, text
from database.exceptions import CampaignNotFoundException, CustomDBExceptions
from database.models import Campaign, CampaignTrigger, CampaignTriggerLink
from typing import Literal


class CampaignsDBInterface(BaseInterface):
    def __init__(
        self,
        db_url: str = None,
        session_: AsyncSession = None
    ):
        super().__init__(db_url=db_url, session_ = session_)
    
    
    async def delete(self, campaign_id: int):
        try:
            await self.delete_rows(
                Campaign,
                id=campaign_id
            )
        except NoResultFound:
            raise CampaignNotFoundException(message=f'Campaign with (id={campaign_id}) is not found')
    
    
    async def update(self, campaign_id: int, **new_data):
        try:
            triggers = new_data.pop("triggers", None)
            await self.update_rows(
                Campaign,
                filter_by={'id': campaign_id},
                **new_data
            )
            await self.delete_rows(
                CampaignTriggerLink,
                campaign_id = campaign_id
            )
            if triggers:
                await self.add_rows(
                    [
                        CampaignTriggerLink(
                            campaign_id=campaign_id,
                            trigger_id=trigger_data['id'],
                            trigger_params=trigger_data.get('trigger_params', None)
                        )
                        for trigger_data in triggers
                    ]
                )
            result = await self.get_all(campaign_id=campaign_id)
        except NoResultFound as ex:
            raise CampaignNotFoundException(message=f'Campaign with (id={campaign_id}) is not found')
        except SQLAlchemyError as ex:
            raise CampaignNotFoundException(message=ex._message())
        return result[0] if result is not None else None
            
    
    async def add(self, campaign_data: dict):
        async with self.async_ses() as session:
            try:
                campaign = Campaign(
                    name=campaign_data['name'],
                    type=campaign_data['type'],
                    title=campaign_data.get('title'),
                    text=campaign_data['text'],
                    button_text=campaign_data.get('button_text'),
                    button_url=campaign_data.get('button_url'),
                    timer=campaign_data.get('timer'),
                    shedulet_at=campaign_data['shedulet_at'],
                    is_active=campaign_data.get('is_active', True),
                    photo=campaign_data.get('photo'),
                )
                session.add(campaign)
                await session.commit()


                # Создание и добавление триггеров
                for trigger_data in campaign_data["triggers"]:
                    # Связь кампании с триггером
                    campaign_trigger_link = CampaignTriggerLink(
                        campaign_id=campaign.id,
                        trigger_id=trigger_data['id'],
                        trigger_params=trigger_data.get('trigger_params', None)
                    )
                    session.add(campaign_trigger_link)

                await session.commit()        
        
                result = await self.get_all(campaign_id=campaign.id)
            except NoResultFound as ex:
                raise CampaignNotFoundException(message=f'Campaign with (id={campaign.id}) is not found')
            except SQLAlchemyError as ex:
                raise CampaignNotFoundException(message=ex._message())
        return result[0] if result is not None else None


    async def get_count(
        self,
        campaign_id: int | None = None,
        is_active: bool | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        name: str | None = None,
    ) -> int:
        async with self.async_ses() as session:
            params = {}
            filters = []

            if campaign_id is not None:
                filters.append('c.id = :campaign_id')
                params['campaign_id'] = campaign_id
            if is_active is not None:
                filters.append('c.is_active = :is_active')
                params['is_active'] = is_active
            if start_date is not None:
                filters.append('c.shedulet_at >= :start_date')
                params['start_date'] = start_date
            if end_date is not None:
                filters.append('c.shedulet_at <= :end_date')
                params['end_date'] = end_date
            if name is not None:
                filters.append('c.name ILIKE :name')
                params['name'] = f"%{name}%"

            filters_str = ""
            if filters:
                filters_str = "WHERE " + " AND ".join(filters)

            result = await session.execute(
                text(
                    f'''
                    SELECT COUNT(DISTINCT c.id) as total
                    FROM campaigns c
                    {filters_str}
                    '''
                ),
                params=params
            )

            return result.scalar_one()
    
    
    async def get_triggers(self):
        return await self.get_rows(
            CampaignTrigger
        )
    
    
    async def get_all(
        self,
        page: int = 1,
        per_page: int = 10,
        order_by: Literal['id'] = "id",
        order_direction: Literal['desc', 'asc'] = 'desc',
        campaign_id: int | None = None,
        is_active: bool | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        name: str | None = None
    ):
        async with self.async_ses() as session:
            params={
                "offset": (page-1)*per_page,
                "limit": per_page
            }

            match order_by:
                case 'id':
                    order_by = 'c.id'
                case _:
                    order_by = 'c.id'
            filters = []
            if campaign_id is not None:
                filters.append('c.id=:campaign_id')
                params['campaign_id'] = campaign_id
            if is_active is not None:
                filters.append(f'c.is_active=:is_active')
                params['is_active'] = is_active
            if start_date is not None:
                filters.append('c.shedulet_at>=:start_date')
                params['start_date'] = start_date
            if end_date is not None:
                filters.append(f'c.shedulet_at<=:end_date')
                params['end_date'] = end_date
            if name is not None:
                filters.append(f"c.name ILIKE :name")
                params['name'] = f"%{name}%"
                
            filters_str = ""
            if filters:
                filters_str = "WHERE " + " AND ".join(filters)
                
            logger.debug(filters_str)
            logger.debug(params)
            query = f'''
            SELECT 
                c.*,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', t.id,
                            'name', t.name,
                            'cron_expression', t.cron_expression,
                            'trigger_params', ctl.trigger_params
                        )
                    ) FILTER (
                        WHERE t.id IS NOT NULL 
                        OR t.name IS NOT NULL 
                        OR t.cron_expression IS NOT NULL 
                        OR ctl.trigger_params IS NOT NULL
                    ),
                    '[]'::json
                ) AS triggers
            FROM campaigns c
            LEFT JOIN campaigns_triggers_link ctl ON ctl.campaign_id = c.id
            LEFT JOIN campaigns_triggers t ON ctl.trigger_id = t.id 
            {filters_str}
            GROUP BY c.id, c.name
            order by {order_by} {'desc' if order_direction == 'desc' else ''}
            offset :offset
            limit :limit
            '''
            logger.debug(query)
            result = await session.execute(
                text(query),
                params=params
            )
            
        return result.mappings().all()
        
    
    async def get_evryday_reward_users_pool(self) -> list[str]:
        async with self.async_ses() as session:
            result = await session.scalars(
                text(
                    '''
                    select
                        distinct on (u.id) 
                        u.tg_id
                    from 
                        users_balances_history as ubh
                    join users u on
                        u.id != ubh.user_id
                    where 
                        ubh.created_at::date = :today
                        and 
                        ubh.reason like('%Everyday reward%')
                        and 
                        u.tg_id is not null
                    '''
                ),
                params={'today': datetime.today().date()}
            )
        return result.all()
    
    
    async def get_users_inactive(self, inactive_days: int):        
        date_limit = datetime.now().date() - timedelta(days=inactive_days)
        async with self.async_ses() as session:
            result = await session.execute(
                text(
                    '''
                    SELECT
                    u.tg_id
                    FROM users u
                    JOIN users_statistic us ON us.user_id = u.id
                    WHERE 
                        u.tg_id IS NOT NULL
                        AND
                        DATE(us.created_at) = (
                            SELECT MAX(DATE(created_at))
                            FROM users_statistic us2
                            WHERE DATE(us2.created_at) < :date_limit
                        );
                    '''
                ),
                params={'date_limit': date_limit}
            )
        return result.mappings().all()
    
    
    async def get_users_inactive(self, task_id: int):        
        async with self.async_ses() as session:
            result = await session.execute(
                text(
                    '''
                    WITH users_completed_tasks AS (
                        SELECT
                            utc.task_template_id,
                            utc.user_id, 
                            COUNT(*) AS user_completed
                        FROM user_tasks_complete utc 
                        JOIN tasks_templates tt ON tt.id = utc.task_template_id
                        GROUP BY utc.task_template_id, utc.user_id
                    ), 
                    tasks_count AS (
                        SELECT 
                            uct.user_id, 
                            uct.task_template_id, 
                            uct.user_completed, 
                            tt.complete_count
                        FROM users_completed_tasks uct
                        JOIN tasks_templates tt ON tt.id = uct.task_template_id
                    )
                    SELECT u.tg_id
                    FROM tasks_count tc
                    join users u on u.id = tc.user_id
                    WHERE task_template_id = :task_template_id
                    AND tc.user_completed < tc.complete_count
                    and u.tg_id is not null
                    ;
                    '''
                ),
                params={'task_id': task_id}
            )
        return result.mappings().all()
    
    
    
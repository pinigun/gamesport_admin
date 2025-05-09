from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_interface import BaseInterface, text
from database.models import Campaign, CampaignTrigger, CampaignTriggerLink


class CampaignsDBInterface(BaseInterface):
    def __init__(
        self,
        db_url: str = None,
        session_: AsyncSession = None
    ):
        super().__init__(db_url=db_url, session_ = session_)

    
    async def update(self, campaign_id: int, **new_data):
        await self.update_rows(
            Campaign,
            filter_by={'id': campaign_id},
            **new_data
        )
        return await self.get_all(campaign_id=campaign_id)


    async def add(self, campaign_data: dict):
        async with self.async_ses() as session:
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
        return await self.get_all(campaign_id=campaign.id)


    async def get_count(self):
        return await self.get_rows_count(Campaign)
    
    
    async def get_triggers(self):
        return await self.get_rows(
            CampaignTrigger
        )
    
    
    async def get_all(
        self,
        page: int =1,
        per_page: int = 10,
        is_active: bool | None = None,
        campaign_id: int | None = None,
    ):
        async with self.async_ses() as session:
            params={
                "offset": (page-1)*per_page,
                "limit": per_page
            }
            if is_active is not None:
                params['is_active'] = is_active
            if campaign_id is not None:
                params['campaign_id'] = campaign_id
            result = await session.execute(
                text(
                    f'''
                    SELECT 
                        c.*,
                        json_agg(
                            json_build_object(
                                'id', t.id,
                                'name', t.name,
                                'cron_expression', t.cron_expression,
                                'trigger_params', ctl.trigger_params
                            )
                        ) AS triggers
                    FROM campaigns c
                    JOIN campaigns_triggers_link ctl ON ctl.campaign_id = c.id
                    JOIN campaigns_triggers t ON ctl.trigger_id = t.id 
                    {f'WHERE c.is_active=:is_active' if is_active is not None else ''} {f'{'WHERE' if is_active is None else 'AND'} c.id=:campaign_id' if campaign_id is not None else ''}
                    GROUP BY c.id, c.name
                    offset :offset
                    limit :limit
                    '''
                ),
                params=params
            )
            
        return result.mappings().all() if campaign_id is None else result.mappings().first()
        
    
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
    
    
    
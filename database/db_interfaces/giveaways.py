from typing import TypedDict
from database.db_interface import BaseInterface
from database.exceptions import FAQNotFound
from database.models import FAQ, Giveaway
from sqlalchemy import select, text, update


class GiveawaysDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
        

    async def get_all(
        self,
        page: int,
        per_page: int
    ):
        async with self.async_ses() as session:
            result = await session.execute(
                text(
                    '''
                    with giveaways_participants_count as (
                        select giveaway_id, count(*) as participants_count
                        from giveaways_participant
                        group by giveaway_id
                    ),
                    last_winners as (
                        select distinct on (ge.giveaway_id)
                            ge.giveaway_id,
                            ge.winner_id
                        from giveaways_ended ge
                        order by ge.giveaway_id, ge.end_date desc
                    )
                    select 
                        g.id, 
                        g.start_date,
                        g.id as number,
                        g.period_days,
                        g.name,
                        g.price,
                        g.active,
                        lw.winner_id,
                        coalesce(participants.participants_count, 0),
                        (coalesce(participants.participants_count, 0) * g.price) as spent_tickets,
                        g.photo
                    from giveaways g
                    left join giveaways_participants_count participants on participants.giveaway_id = g.id
                    left join last_winners lw on lw.giveaway_id = g.id
                    order by g.id, g.active
                    limit :limit
                    offset :offset;
                    '''
                ),
                {
                    "limit": per_page,
                    "offset": (page-1) * per_page
                }
            )
            
            return result.mappings().all()
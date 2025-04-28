from datetime import datetime
import os
from fastapi import UploadFile
from loguru import logger
from api.routers.giveaways.schemas import Giveaway, GiveawayHistoryRecord, GiveawayParticiptant, GiveawayPrize
from tools.photos import PhotoTools
from database import db


class GiveawaysTools:
    async def add_winner(
        giveaway_id:    int,
        winner_id:      int,
        prize_id:       int
    ):
        await db.giveaways.add_winner(
            giveaway_id,
            winner_id,
            prize_id
        )
    
    
    async def get_participants(
        page: int,
        per_page: int,
        giveaway_id: int,
        start_date: datetime,
        end_date: datetime | None = None,
    ) -> list[GiveawayParticiptant]:
        return [
            GiveawayParticiptant.model_validate(participtant)
            for participtant in await db.giveaways.get_participtants(
                page=page,
                per_page=per_page,
                giveaway_id=giveaway_id,
                start_date=start_date,
                end_date=end_date,
            )
        ]
        
        
    async def get_prizes(giveaway_id: int, page: int, per_page: int):
        return [
            GiveawayPrize.model_validate(prize)
            for prize in await db.giveaways.get_prizes(giveaway_id=giveaway_id, page=page, per_page=per_page)
        ]
    
    
    async def get_participants_count(
        giveaway_id: int,
        start_date: datetime,
        end_date: datetime | None = None                                 
    ):
        return await db.giveaways.get_participants_count(giveaway_id, start_date, end_date)
    
    
    async def get_history_count():
        return await db.giveaways.get_history_count()
    
    
    async def get_prizes_count(giveaway_id: int):
        return await db.giveaways.get_prizes_count(giveaway_id)
    
    
    async def get_giveaways_count():
        return await db.giveaways.get_giveaways_count()
    
    
    async def get_history(
        page: int,
        per_page: int
    ) -> list[GiveawayHistoryRecord]:
        return [
            GiveawayHistoryRecord(**dict(giveaway_hr))
            for giveaway_hr in await db.giveaways.get_history(page, per_page)
        ]
    # async def add_prize(giveaway_id: int, **prize_data):
    #     photo = prize_data.pop('photo', None)
        
    #     new_prize = await db.giveaways.add(**prize_data)
        
    #     photo_path = f'static/prizes/{giveaway_id}'
    #     os.makedirs(photo_path, exist_ok=True)
    #     photo_path = await PhotoTools.save_photo(path=photo_path, photo=photo, filename=new_prize.id)
    #     await db.giveaways.update_prize(
    #         giveaway_id=giveaway_id,
    #         prize_id=new_prize.id,
    #         photo=photo_path
    #     )
    #     new_info = await db.giveaways.get_all(giveaway_id=giveaway_id)
    #     return Giveaway(**new_info)
    
    
    async def add(**new_giveaway_data):
        photo = new_giveaway_data.pop('photo', None)
        
        new_giveaway = await db.giveaways.add(**new_giveaway_data)
        
        os.makedirs(f'static/giveaways/{new_giveaway.id}', exist_ok=True)
        photo_path = await PhotoTools.save_photo(path=f'static/giveaways/{new_giveaway.id}', photo=photo)
        await db.giveaways.update(
            giveaway_id=new_giveaway.id,
            photo=photo_path
        )
        new_info = await db.giveaways.get_all(giveaway_id=new_giveaway.id)
        return Giveaway(**new_info)
        
    
    async def update(giveaway_id: int, **new_giveaway_data):
        photo = new_giveaway_data.pop('photo', None)
        if photo:
            os.makedirs(f'static/giveaways/{giveaway_id}', exist_ok=True)
            await PhotoTools.save_photo(path=f'static/giveaways/{giveaway_id}', photo=photo)
            
        await db.giveaways.update(
            giveaway_id=giveaway_id,
            **{key: value for key, value in new_giveaway_data.items() if value is not None}
        )
        new_info = await db.giveaways.get_all(giveaway_id=giveaway_id)
        return Giveaway(**new_info)
    
    
    async def get(giveaway_id: int) -> Giveaway:
        return Giveaway.model_validate(dict(
            await db.giveaways.get_all(giveaway_id=giveaway_id)
        ))
    
    
    async def get_all(
        page: int,
        per_page: int
    ) -> list[Giveaway]:
        return [
            Giveaway.model_validate(dict(giveaway))
            for giveaway in await db.giveaways.get_all(
                page=page,
                per_page=per_page
            )
        ]
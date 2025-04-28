import os
from loguru import logger
from api.routers.giveaways.schemas import Giveaway
from tools.photos import PhotoTools
from database import db


class GiveawaysTools:
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
            photo_path = await PhotoTools.save_photo(path=f'static/giveaways/{giveaway_id}', photo=photo)
            
        await db.giveaways.update(
            giveaway_id=giveaway_id,
            **{key: value for key, value in new_giveaway_data.items() if value is not None}
        )
        new_info = await db.giveaways.get_all(giveaway_id=giveaway_id)
        return Giveaway(**new_info)
    
    
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
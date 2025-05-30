import asyncio
import io
import os
from fastapi import UploadFile
from loguru import logger
import pandas as pd
from config import BASE_ADMIN_URL
from database import db
from datetime import datetime
from tools.photos import PhotoTools
from api.routers.giveaways.schemas import Giveaway, GiveawayHistoryRecord, GiveawayParticiptant, GiveawayPrize, Prize, PrizesData


class GiveawaysTools:
    async def get_participants_report(data: list[GiveawayParticiptant]) -> io.BytesIO:
        if len(data) > 0:
            df = pd.DataFrame([row.model_dump() for row in data])
        else:
            # Создаем DataFrame с колонками из Pydantic-модели
            df = pd.DataFrame(columns=GiveawayParticiptant.model_fields.keys())
        # Записываем в память (в буфер)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)  # возвращаемся в начало буфера

        # Отправляем как файл
        return output
    
    
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
        **kwargs
    ) -> list[GiveawayParticiptant]:
        return [
            GiveawayParticiptant.model_validate(participtant)
            for participtant in await db.giveaways.get_participtants(
                page=page,
                per_page=per_page,
                giveaway_id=giveaway_id,
                start_date=start_date,
                end_date=end_date,
                **kwargs
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
        page:               int,
        per_page:           int,
        order_by:           str | None,
        order_direction:    str | None
    ) -> list[GiveawayHistoryRecord]:
        return [
            GiveawayHistoryRecord(**dict(giveaway_hr))
            for giveaway_hr in await db.giveaways.get_history(page, per_page, order_by, order_direction)
        ]
            
    
    async def add_prizes(
        giveaway_id: int,
        prizes_data: list[Prize],
        prizes_photos: list[UploadFile]
    ):
        prizes_data: list[dict] = [
            prize.model_dump(exclude=['id'])
            for prize in prizes_data
        ]
        prizes=await db.giveaways.add_prizes(
            giveaway_id=giveaway_id,
            prizes_data=prizes_data
        )
        photos_paths = await asyncio.gather(
            *[
                PhotoTools.save_photo(
                    path=f'static/giveaways/{giveaway_id}', 
                    photo=photo,
                    filename=str(prizes[i].id)
                )
                for i, photo in enumerate(prizes_photos)
            ]
        )
        for i, prize in enumerate(prizes):
            prize.photo = photos_paths[i]
            await db.giveaways.update_prize(
                prize_id=prize.id,
                giveaway_id=giveaway_id,
                photo=photos_paths[i]
            )
    
    
    async def add(**new_giveaway_data) -> Giveaway:
        prizes_data=new_giveaway_data.pop('prizes_data').prizes
        prizes_photos=new_giveaway_data.pop('prizes_photos')
        new_giveaway = await db.giveaways.add(**new_giveaway_data) 
        
        await GiveawaysTools.add_prizes(
            giveaway_id=new_giveaway.id,
            prizes_data=prizes_data,
            prizes_photos=prizes_photos,
        )
        
        return await GiveawaysTools.get(giveaway_id=new_giveaway.id)
        
    
    async def update(giveaway_id: int, **new_giveaway_data):
        prizes_data = new_giveaway_data.pop('prizes_data').prizes
        prizes_photos: list[UploadFile] = new_giveaway_data.pop('prizes_photos')
        logger.debug(f"{prizes_data=}")
        logger.debug(f"{prizes_photos=}")
        new_prizes = []
        new_photos = []
        old_prizes = []
        old_photos = []
        for i, prize in enumerate(prizes_data):
            if prize.id is None:
                new_prizes.append(prize)
                new_photos.append(prizes_photos[i])
            else:
                old_prizes.append(prize)
                old_photos.append(prizes_photos[i])
        
        prizes_data = old_prizes
        prizes_photos = old_photos
                    
        curr_giveaway_prizes = {
            prize['id']: prize
            for prize in dict(await db.giveaways.get_all(giveaway_id=giveaway_id))['prizes']
        }
        curr_giveaway_prizes_ids = curr_giveaway_prizes.keys()
        
        # если у нас удалили какой то приз, то удаляем его из бд
        if len(prizes_data) < len(curr_giveaway_prizes):
            new_giveaway_prizes_ids = {
                prize.id
                for prize in prizes_data
            }
            needed_delete_ids = set(curr_giveaway_prizes_ids) - set(new_giveaway_prizes_ids)
            for prize_id in needed_delete_ids:
                await db.giveaways.delete_prize(prize_id)
                logger.debug(curr_giveaway_prizes[prize_id]['photo'])
                if curr_giveaway_prizes[prize_id]['photo'] is not None:
                    await PhotoTools.delete_file(
                        file_path=curr_giveaway_prizes[prize_id]['photo']
                    )
                
        for i, prize in enumerate(prizes_data):
            logger.debug(f"{prize=}")
            await db.giveaways.update_prize(
                prize_id = prize.id,
                giveaway_id=giveaway_id,
                **prize.model_dump(exclude=['id'])
            )
            await PhotoTools.save_photo(
                path=f'static/giveaways/{giveaway_id}',
                photo=prizes_photos[i],
                filename=prize.id
            )
                
        await GiveawaysTools.add_prizes(
            giveaway_id=giveaway_id,
            prizes_data=new_prizes,
            prizes_photos=new_photos
        )
            
        await db.giveaways.update(
            giveaway_id=giveaway_id,
            **{key: value for key, value in new_giveaway_data.items() if value is not None}
        )
        return await GiveawaysTools.get(giveaway_id=giveaway_id)
    
    
    async def get(giveaway_id: int) -> Giveaway:
        result = dict(
            await db.giveaways.get_all(giveaway_id=giveaway_id)
        )
        for i, prize in enumerate(result['prizes']):
            prize['photo'] = f"{BASE_ADMIN_URL}/{prize['photo']}" if prize['photo'] else None
        return Giveaway.model_validate(
            result
        )
    
    
    async def get_all(
        page: int,
        per_page: int,
        order_by: str | None,
        order_direction: str | None
    ) -> list[Giveaway]:
        return [
            Giveaway.model_validate(dict(giveaway))
            for giveaway in await db.giveaways.get_all(
                page=page,
                per_page=per_page,
                order_by=order_by,
                order_direction=order_direction
            )
        ]
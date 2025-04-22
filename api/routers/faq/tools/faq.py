from api.routers.admins.tools.admins import db
from api.routers.faq.schemas import FAQData, FAQResponse


class FAQTools:
    async def delete(faq_id: int):
        return await db.faq.delete(faq_id) 
                
    
    async def get_count():
        return await db.faq.get_count()
    
    
    async def add(faq_data: FAQData):
        return await db.faq.add(faq_data.model_dump())
    
    
    async def update(faq_id: int, faq_data: FAQData):
        return await db.faq.update(faq_id, faq_data.model_dump())
    
    
    async def get_all(page: int, per_page: int) -> list[FAQResponse]:
        return [
            FAQResponse.model_validate(faq)
            for faq in await db.faq.get_all(page, per_page)
        ]
        
    
    async def swap(first_faq_id: int, second_faq_id) -> list[FAQResponse]:
        return [
            FAQResponse.model_validate(faq)
            for faq in await db.faq.swap(first_faq_id, second_faq_id)
        ]

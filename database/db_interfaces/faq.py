from typing import TypedDict
from database.db_interface import BaseInterface
from database.exceptions import FAQNotFound
from database.models import FAQ
from sqlalchemy import select, text, update


class FAQSwapDict(TypedDict):
    faq_id:             int
    faq_curr_position:  int


class FAQDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
        
        
    async def swap(self, first_faq_id: int, second_faq_id: int):
        async with self.async_ses() as session:
            faqs = await session.execute(
                select(FAQ)
                .where(FAQ.id.in_([first_faq_id, second_faq_id]))
            )
            faqs = faqs.scalars().all()
            if len(faqs) < 2:
                if len(faqs) == 0:
                    raise FAQNotFound(
                        message=FAQNotFound.message.format(faq_id=first_faq_id)
                    )
                else:
                    raise FAQNotFound(
                        message=FAQNotFound.message.format(faq_id=first_faq_id if faqs[0].id == second_faq_id else second_faq_id)
                    )
            
            faqs[0].position, faqs[1].position = faqs[1].position, faqs[0].position 
            
            await session.commit()
            await session.refresh(faqs[0])        
            await session.refresh(faqs[1])
            return faqs        
        
        
    async def delete(self, faq_id: int):
        await self.delete_rows(FAQ, id=faq_id)
        
    
    async def update(self, faq_id: int, faq_data: dict):
        return await self.update_rows(FAQ, filter_by={'id': faq_id}, **faq_data)    
        
        
    async def get_count(self):
        return await self.get_rows_count(FAQ)
    
    
    async def get_all(
        self,
        page: int,
        per_page: int
    ):
        return await self.get_rows(
            FAQ,
            offset=(page - 1) * per_page,
            limit=per_page,
            order_by='position'
        )
        
        
    async def add(self, faq_data: dict) -> FAQ:
        async with self.async_ses() as session:
            await session.execute(
                text('UPDATE faq SET position = position + 1')
            )
            session.add(
                FAQ(**faq_data)
            )
            await session.commit()

    
    async def swap_faqs(
        self,
        first_faq: FAQSwapDict,
        second_faq: FAQSwapDict
    ):
        '''Swap two faqs'''
        ...
        
    
    async def edit(self, faq_data):
        ...
        
    
        
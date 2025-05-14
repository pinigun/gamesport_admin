from typing import TypedDict
from database.db_interface import BaseInterface
from database.exceptions import DocsNotFound
from database.models import DocAndRule
from sqlalchemy import select, text, update


class DocsSwapDict(TypedDict):
    doc_id:             int
    doc_curr_position:  int


class DocsDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
        
        
    async def swap(self, first_doc_id: int, second_doc_id: int):
        async with self.async_ses() as session:
            docs = await session.execute(
                select(DocAndRule)
                .where(DocAndRule.id.in_([first_doc_id, second_doc_id]))
            )
            docs = docs.scalars().all()
            if len(docs) < 2:
                if len(docs) == 0:
                    raise DocsNotFound(
                        message=DocsNotFound.message.format(doc_id=first_doc_id)
                    )
                else:
                    raise DocsNotFound(
                        message=DocsNotFound.message.format(
                            doc_id=first_doc_id 
                            if docs[0].id == second_doc_id 
                            else second_doc_id
                        )
                    )
            
            docs[0].position, docs[1].position = docs[1].position, docs[0].position 
            
            await session.commit()
            await session.refresh(docs[0])        
            await session.refresh(docs[1])
            return docs        
        
        
    async def delete(self, doc_id: int):
        await self.delete_rows(DocAndRule, id=doc_id)
        
    
    async def update(self, doc_id: int, doc_data: dict):
        return await self.update_rows(DocAndRule, filter_by={'id': doc_id}, **doc_data)    
        
        
    async def get_count(self):
        return await self.get_rows_count(DocAndRule)
    
    
    async def get_all(
        self,
        page: int,
        per_page: int
    ):
        return await self.get_rows(
            DocAndRule,
            offset=(page - 1) * per_page,
            limit=per_page,
            order_by='position'
        )
        
        
    async def add(self, doc_data: dict) -> DocAndRule:
        async with self.async_ses() as session:
            await session.execute(
                text('UPDATE docs_and_rules SET position = position + 1')
            )
            doc = DocAndRule(**doc_data) 
            session.add(doc)
            await session.commit()
            return doc
        
    
        
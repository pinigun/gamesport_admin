from api.routers.admins.tools.admins import db
from api.routers.docs.schemas import DocsData, DocsResponse


class DocsTools:
    async def delete(doc_id: int):
        return await db.docs.delete(doc_id) 
                
    
    async def get_count():
        return await db.docs.get_count()
    
    
    async def add(doc_data: DocsData) -> DocsResponse:
        return DocsResponse.model_validate(await db.docs.add(doc_data.model_dump()))
    
    
    async def update(doc_id: int, doc_data: DocsData) -> DocsResponse:
        return DocsResponse.model_validate(await db.docs.update(doc_id, doc_data.model_dump()))
    
    
    async def get_all(page: int, per_page: int) -> list[DocsResponse]:
        return [
            DocsResponse.model_validate(doc)
            for doc in await db.docs.get_all(page, per_page)
        ]
        
    
    async def swap(first_doc_id: int, second_doc_id) -> list[DocsResponse]:
        return [
            DocsResponse.model_validate(doc)
            for doc in await db.docs.swap(first_doc_id, second_doc_id)
        ]

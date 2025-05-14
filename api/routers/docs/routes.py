import math
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import NoResultFound
from api.routers.docs.schemas import DocsData, DocsRequest, DocsResponse, SwapDocsRequest
from api.routers.docs.tools.docs import DocsTools
from database.exceptions import CustomDBExceptions


router = APIRouter(
    tags=['Docs & Rules'],
    prefix='/docs_rules',
)


@router.get('/')
async def get_docs(
    page: int = 1,
    per_page: int = 12,
) -> DocsData:
    total_items = await DocsTools.get_count()
    total_pages = math.ceil(total_items / per_page)
    
    return DocsData(
        total_pages=total_pages,
        total_items=total_items,
        per_page=per_page,
        current_page=page,
        items = await DocsTools.get_all(page, per_page) if total_pages else []
    )
    
    
@router.post('/')
async def add_doc(
    doc_data: DocsRequest
) -> DocsResponse:
    return await DocsTools.add(doc_data)


@router.patch('/swap')
async def swap_docs(
    data: SwapDocsRequest
) -> list[DocsResponse]:
    '''Replacing places for two documentss'''
    try:
        return await DocsTools.swap(data.first_doc_id, data.second_doc_id)
    except CustomDBExceptions as ex:
        raise HTTPException(400, detail=ex.message)


@router.patch('/{doc_id}')
async def edit_doc(
    doc_id: int,
    doc_data: DocsRequest
) -> DocsResponse:
    try:
        return await DocsTools.update(doc_id, doc_data)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f'Docs (id={doc_id}) not found')

    
@router.delete('/{doc_id}')
async def delete_doc(
    doc_id: int
):
    try:
        return await DocsTools.delete(doc_id)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)
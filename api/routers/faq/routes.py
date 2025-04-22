import math
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import NoResultFound

from api.routers.auth.tools.auth import AuthTools
from api.routers.faq.schemas import FAQData, FAQRequest, SwapFAQRequest
from api.routers.faq.tools.faq import FAQTools
from custom_types import PermissionsTags
from database.exceptions import CustomDBExceptions


router = APIRouter(
    tags=['FAQ'],
    prefix='/faq',
)


@router.get('/')
async def get_faq(
    page: int = 1,
    per_page: int = 12,
) -> FAQData:
    total_faqs = await FAQTools.get_count()
    total_pages = math.ceil(total_faqs / per_page)
    
    return FAQData(
        total_pages=total_pages,
        total_items=total_faqs,
        per_page=per_page,
        current_page=page,
        items = await FAQTools.get_all(page, per_page) if total_pages else []
    )
    
    
@router.post('/')
async def add_faq(
    faq_data: FAQRequest
):
    return await FAQTools.add(faq_data)


@router.patch('/swap')
async def swap_faqs(
    data: SwapFAQRequest
):
    '''Replacing places for two faqs'''
    try:
        return await FAQTools.swap(data.first_faq_id, data.second_faq_id)
    except CustomDBExceptions as ex:
        raise HTTPException(400, detail=ex.message)


@router.patch('/{faq_id}')
async def edit_faq(
    faq_id: int,
    faq_data: FAQRequest
):
    try:
        return await FAQTools.update(faq_id, faq_data)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f'FAQ (id={faq_id}) not found')

    
@router.delete('/{faq_id}')
async def delete_faq(
    faq_id: int
):
    try:
        return await FAQTools.delete(faq_id)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)
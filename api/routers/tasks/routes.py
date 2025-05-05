from ast import Str
from datetime import datetime, time
import math
import re
from typing import Literal, Optional, Union
from fastapi import APIRouter, Body, Depends, File, Form, Query, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from api.routers.dashboards.tools.dashboards import DashboardsTools
from api.routers.tasks.schemas import SupportedGiveaway, Task, TasksData
from api.routers.tasks.tools.tasks import TasksTools
from database.exceptions import CustomDBExceptions


router = APIRouter(
    tags=['Tasks'],
    prefix='/tasks',
    # dependencies=[Depends(AuthTools.check_permissions(PermissionsTags.USERS))]
)

@router.get('/')
async def get_tasks(
    page:       int = Query(1, gt=0),
    per_page:   int = Query(10, gt=0),
    task_id:    int | None = None,
    name:       str | None = None,
) -> TasksData:
    total_items = await TasksTools.get_count()
    total_pages = math.ceil(total_items / per_page)
    
    return TasksData(
        total_pages=total_pages,
        total_items=total_items,
        per_page=per_page,
        current_page=page,
        items = await TasksTools.get_all(
            page=page,
            per_page=per_page,
            task_id=task_id,
            name=name
        ) if total_pages else []
    )
    

@router.get('/participants/report/{task_id}')
async def get_participants_report(task_id: int) -> StreamingResponse:
    participants = await TasksTools.get_participants(task_id=task_id)  
    output = await TasksTools.get_participants_report(participants)
    headers = {
        'Content-Disposition': f'attachment; filename="task{task_id}.xlsx"'
    }
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)


@router.post('/task')
async def add_task(
    title:          str = Form(..., description='Название задания'),
    is_active:      bool = Form(..., description="Статус"),
    reward:         Union[int, Literal['']] = Form('', description='Награда в билетах'),
    giveaway_id:    Union[int, Literal['']] = Form('', description='Наградой может быть участие в конкурсе, сюда передаем гивеэвей айди'),
    redirect_url:   Union[str, Literal['']] = Form('', description="Ссылка"),
    check_type:     Literal['auto', 'handle', 'timer', 'postback'] = Form(..., description='Тип проверки'),
    complete_count: Union[int, Literal['']] = Form('', description='Кол-во выполненных задач для завершения задания'),
    description:    str = Form(..., description='Текст задания'),
    timer:          Union[str, Literal['']] = Form('', description='Если выбран check_type="timer", то обязательное поле. Пример: 01:55:15'),
    postback_url:   Union[str, Literal['']] = Form('', description='Если выбран check_type="postback", то обязательное поле.'),
    photo:          Union[UploadFile, Literal['']] = File('')
) -> Task:
    if isinstance(complete_count, int):
        if complete_count < 1:
            raise HTTPException(400, detail='Bad request: complete_count should been >= 1')
        
    if check_type == 'timer':
        if timer == '' or timer is None:
            raise HTTPException(400, detail='Bad request: "timer" is required if check_type="timer"')
        pattern = r'^\d{2}:\d{2}:\d{2}$'
        if not re.match(pattern, timer):
            raise HTTPException(400, detail='Bad request: Timer format: HH:MM:SS')
    
    if check_type == 'postback':
        if postback_url == '' or postback_url is None:
            raise HTTPException(400, detail='Bad request: "postback_url" is required if check_type="postback"')
    if giveaway_id == '' or giveaway_id is None:
        giveaway_id = None
    return await TasksTools.add(
        title=title,
        is_active=is_active,
        reward=reward,
        giveaway_id=giveaway_id,
        redirect_url=redirect_url if redirect_url != '' else None,
        check_type=check_type,
        complete_count=complete_count if complete_count != '' else 1,
        description=description,
        timer=timer if timer != '' else None,
        postback_url=postback_url,
        photo=photo if photo != '' else None
    )
    
    
@router.patch('/{task_id}')
async def edit_task(
    task_id:        int,
    title:          str = Form(..., description='Название задания'),
    is_active:      bool = Form(..., description="Статус"),
    reward:         Union[int, Literal['']] = Form('', description='Награда в билетах'),
    giveaway_id:    Union[int, Literal['']] = Form('', description='Наградой может быть участие в конкурсе, сюда передаем гивеэвей айди'),
    redirect_url:   Union[str, Literal['']] = Form('', description="Ссылка"),
    check_type:     Literal['auto', 'handle', 'timer', 'postback'] = Form(..., description='Тип проверки'),
    complete_count: Union[int, Literal['']] = Form('', description='Кол-во выполненных задач для завершения задания'),
    description:    str = Form(..., description='Текст задания'),
    timer:          Union[str, Literal['']] = Form('', description='Если выбран check_type="timer", то обязательное поле. Пример: 01:55:15'),
    postback_url:   Union[str, Literal['']] = Form('', description='Если выбран check_type="postback", то обязательное поле.'),
    photo:          Union[UploadFile, Literal['']] = File('')
) -> Task:
    if isinstance(complete_count, int):
        if complete_count < 1:
            raise HTTPException(400, detail='Bad request: complete_count should been >= 1')
        
    if check_type == 'timer':
        if timer == '' or timer is None:
            raise HTTPException(400, detail='Bad request: "timer" is required if check_type="timer"')
        pattern = r'^\d{2}:\d{2}:\d{2}$'
        if not re.match(pattern, timer):
            raise HTTPException(400, detail='Bad request: timer format: HH:MM:SS')
    
    if check_type == 'postback':
        if postback_url == '' or postback_url is None:
            raise HTTPException(400, detail='Bad request: "postback_url" is required if check_type="postback"')
        
    return await TasksTools.update(
        task_id =       task_id,
        title=          title if title != '' else None,
        is_active=      is_active if is_active != '' else None,
        reward=         reward if reward != '' else None,
        check_type=     check_type if check_type else None,
        description=    description if description else None,
        redirect_url=   redirect_url if redirect_url != '' else None,
        complete_count= complete_count if complete_count != '' else None,
        photo=          photo if photo != '' else None,
        giveaway_id=    giveaway_id if giveaway_id != '' else None,
        timer=          timer if timer != '' else None,
        postback_url=   postback_url if postback_url != '' else None
    )
    
    
@router.get('/supported_giveaways')
async def get_supported_giveaways() -> list[SupportedGiveaway]:
    return await TasksTools.get_supported_giveaways()
    
    
@router.delete('/{task_id}')
async def delete_task(task_id: int):
    try:
        await TasksTools.delete(task_id)
        return JSONResponse(status_code=200, content={'detail': 'Success'})
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)

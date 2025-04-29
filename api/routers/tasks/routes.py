from datetime import datetime
import math
from fastapi import APIRouter, Depends, Query, HTTPException
from api.routers.tasks.tools.tasks import TasksTools


router = APIRouter(
    tags=['Tasks'],
    prefix='/tasks',
    # dependencies=[Depends(AuthTools.check_permissions(PermissionsTags.USERS))]
)

@router.get('/')
async def get_tasks():
    return await TasksTools.get_all()
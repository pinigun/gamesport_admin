import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from api.routers import api_router
from loguru import logger

app = FastAPI()
api = FastAPI()

api.include_router(api_router)
logger.debug('Teeeeeeeeeeeeeeeeeeest appp')
os.makedirs('static', exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount('/admin_panel', api, "API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"]
)

if __name__ == '__main__':
    
    uvicorn.run(app)
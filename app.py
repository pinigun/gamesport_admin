from fastapi import FastAPI
import uvicorn
from api.routers import api_router

app = FastAPI()
api = FastAPI()

api.include_router(api_router)

app.mount('/admin_panel', api, "API")

if __name__ == '__main__':
    uvicorn.run(app)
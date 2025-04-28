from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.routers import api_router

app = FastAPI(debug=True)
api = FastAPI(debug=True)

api.include_router(api_router)

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
    uvicorn.run(app, log_level='debug')
from fastapi import FastAPI
from app.api.routes import router as api_router
from app.settings import settings



app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")

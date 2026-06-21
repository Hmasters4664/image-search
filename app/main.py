import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import router as api_router
from app.settings import settings
from app.tasks.indexer import indexer_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(indexer_loop(interval_seconds=60))
    yield
    task.cancel()
    await asyncio.shield(task)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")

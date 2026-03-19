from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.dependencies.executor import get_executor, shutdown_executor
from app.api.routers.report_router import router as report_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализируем пул процессов при старте
    get_executor()
    yield
    # Плавно завершаем при остановке
    shutdown_executor()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Word Frequency Report API",
        description="Частотный анализ текстовых файлов с экспортом в xlsx",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(report_router)
    return app


app = create_app()

"""FastAPI 应用入口：挂载 OpenAI 兼容与自定义路由。"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.custom_api import router as custom_router
from app.api.openai_compat import router as openai_router
from app.api.voices import router as voices_router


def create_app() -> FastAPI:
    app = FastAPI(title="TTS Service", version="0.1.0")

    app.include_router(openai_router)
    app.include_router(custom_router)
    app.include_router(voices_router)

    return app


app = create_app()

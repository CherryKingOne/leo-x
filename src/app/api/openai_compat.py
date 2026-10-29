"""OpenAI 兼容接口：/v1/audio/speech, /v1/models。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import OpenAIModel, OpenAIModelsResponse, OpenAISpeechRequest
from app.tts.engine import TTSEngine

router = APIRouter(prefix="/v1", tags=["openai-compat"])

engine_instance: TTSEngine | None = None


def get_engine() -> TTSEngine:
    global engine_instance
    if engine_instance is None:
        engine_instance = TTSEngine()
    return engine_instance


@router.post("/audio/speech")
async def audio_speech(req: OpenAISpeechRequest):
    """文本转语音（OpenAI 兼容）。返回音频二进制流。"""
    engine = get_engine()
    try:
        result = engine.synthesize(
            text=req.input,
            model_id=req.model,
            format=req.response_format,
            speed=req.speed,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))

    audio_bytes = engine.to_bytes(result)

    media_type = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "pcm": "application/octet-stream",
    }.get(req.response_format, "application/octet-stream")

    return StreamingResponse(iter([audio_bytes]), media_type=media_type)


@router.get("/models", response_model=OpenAIModelsResponse)
async def list_models():
    """列出可用模型（OpenAI 格式）。"""
    import time

    from app.tts.manager import ModelManager

    manager = ModelManager()
    infos = manager.list_models()
    now = int(time.time())
    data = [OpenAIModel(id=m.model_id, created=now) for m in infos]
    return OpenAIModelsResponse(data=data)

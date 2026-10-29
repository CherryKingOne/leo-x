"""自定义接口：/api/v1/tts/* 合成、引擎、模型管理。"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    EngineInfo,
    EnginesResponse,
    ModelClearRequest,
    ModelDownloadRequest,
    ModelInfo,
    ModelsResponse,
    TTSSynthesizeRequest,
)
from app.tts.engine import TTSEngine

router = APIRouter(prefix="/api/v1/tts", tags=["custom-tts"])

engine_instance: TTSEngine | None = None


def get_engine() -> TTSEngine:
    global engine_instance
    if engine_instance is None:
        engine_instance = TTSEngine()
    return engine_instance


@router.post("/synthesize")
async def synthesize(req: TTSSynthesizeRequest):
    """文本合成（支持 URL 音色克隆 / 已注册 voice_id）。返回音频流。"""
    engine = get_engine()
    try:
        result = engine.synthesize(
            text=req.text,
            model_id=req.engine,
            voice_id=req.voice_id,
            reference_audio=None,
            format=req.format,
            speed=req.speed,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))

    audio_bytes = engine.to_bytes(result)
    media_type = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
    }.get(req.format, "application/octet-stream")
    return StreamingResponse(iter([audio_bytes]), media_type=media_type)


@router.post("/synthesize-upload")
async def synthesize_upload(
    text: str = Form(...),
    engine: str = Form(...),
    voice_id: str | None = Form(None),
    voice: str | None = Form(None),
    format: str = Form("wav"),
    speed: float = Form(1.0),
    reference_audio: UploadFile | None = File(None),
):
    """文本合成（上传参考音频文件，multipart/form-data）。返回音频流。"""
    tts_engine = get_engine()
    ref_bytes: bytes | None = None
    if reference_audio is not None:
        ref_bytes = await reference_audio.read()

    try:
        result = tts_engine.synthesize(
            text=text,
            model_id=engine,
            voice_id=voice_id,
            reference_audio=ref_bytes,
            format=format,
            speed=speed,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))

    audio_bytes = tts_engine.to_bytes(result)
    media_type = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
    }.get(format, "application/octet-stream")
    return StreamingResponse(iter([audio_bytes]), media_type=media_type)


@router.get("/engines", response_model=EnginesResponse)
async def list_engines():
    """列出所有可用模型（对外统一称为 engines，均位于 models/tts/ 下）。"""
    from app.tts.manager import ModelManager

    manager = ModelManager()
    entries = manager.list_models()
    engines = [
        EngineInfo(
            name=e.model_id,
            description=f"{e.display_name or e.model_id} TTS",
            voices=[],
            supports_voice_clone=True,
        )
        for e in entries
    ]
    return EnginesResponse(engines=engines)


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """列出所有模型及其下载状态（来自 models/tts/models.json 映射表）。"""
    from app.tts.manager import ModelManager

    manager = ModelManager()
    entries = manager.list_models()
    models = [
        ModelInfo(
            id=e.model_id,
            display_name=e.display_name,
            engine=e.model_id,
            path=str(e.local_path) if e.local_path else None,
            size_bytes=e.size_bytes,
            downloaded=e.downloaded,
            downloaded_at=None,
        )
        for e in entries
    ]
    return ModelsResponse(models=models)


@router.post("/models/download")
async def download_model(req: ModelDownloadRequest):
    """下载模型（huggingface_hub，带进度条）。model_id 支持 display_name（如 voxcpm-2.0）。"""
    from app.tts.manager import ModelManager

    manager = ModelManager()
    try:
        path = manager.download_model(model_id=req.model_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))
    entry = manager.get_mapping().get(req.model_id)
    return {
        "model_id": req.model_id,
        "display_name": entry.display_name if entry else req.model_id,
        "engine": req.model_id,
        "status": "downloaded",
        "path": str(path),
    }


@router.post("/models/clear")
async def clear_model(req: ModelClearRequest):
    """清理模型缓存。"""
    from app.tts.manager import ModelManager

    manager = ModelManager()
    removed = manager.clear_model(model_id=req.model_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"模型未找到: {req.model_id}")
    return {"model_id": req.model_id, "status": "cleared"}

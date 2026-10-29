"""自定义声音接口：/api/v1/tts/voices 注册、列表、删除。"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.schemas import (
    VoiceRecord,
    VoiceRegisterResponse,
    VoicesResponse,
)
from app.tts.engine import TTSEngine

router = APIRouter(prefix="/api/v1/tts/voices", tags=["custom-voices"])

engine_instance: TTSEngine | None = None


def get_engine() -> TTSEngine:
    global engine_instance
    if engine_instance is None:
        engine_instance = TTSEngine()
    return engine_instance


@router.post("", response_model=VoiceRegisterResponse)
async def register_voice(
    name: str = Form(...),
    engine: str = Form(...),
    description: str = Form(""),
    expire_days: int = Form(7),
    reference_audio: UploadFile = File(...),
):
    """注册自定义声音（音色复刻），返回 voice_id。创建一次，后续复刻直接用 id。"""
    tts_engine = get_engine()
    suffix = Path(reference_audio.filename or "ref.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(reference_audio.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        record = tts_engine.register_voice(
            name=name,
            engine=engine,
            reference_audio_path=tmp_path,
            description=description,
            expire_days=expire_days,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    return VoiceRegisterResponse(
        voice_id=record.voice_id,
        name=record.name,
        engine=record.engine,
        description=record.description,
        audio_path=str(record.audio_path),
        expire_days=record.expire_days,
        expires_at=record.expires_at,
        created_at=record.created_at,
    )


@router.get("", response_model=VoicesResponse)
async def list_voices():
    """列出所有已注册的自定义声音。"""
    tts_engine = get_engine()
    records = tts_engine.list_voices()
    return VoicesResponse(
        voices=[
            VoiceRecord(
                voice_id=r.voice_id,
                name=r.name,
                engine=r.engine,
                description=r.description,
                audio_path=str(r.audio_path),
                expire_days=r.expire_days,
                expires_at=r.expires_at,
                created_at=r.created_at,
            )
            for r in records
        ]
    )


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """删除自定义声音。"""
    tts_engine = get_engine()
    removed = tts_engine.delete_voice(voice_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"声音未找到: {voice_id}")
    return {"voice_id": voice_id, "status": "deleted"}

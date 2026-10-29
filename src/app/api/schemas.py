"""Pydantic 请求/响应模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------- OpenAI 兼容 ----------
class OpenAISpeechRequest(BaseModel):
    model: str = Field(..., description="模型名")
    input: str = Field(..., description="待合成文本")
    voice: str | None = Field(None, description="说话人/音色标识")
    response_format: str = Field("mp3", description="输出格式 mp3/wav/ogg/flac/pcm")
    speed: float = Field(1.0, ge=0.25, le=4.0, description="语速")


class OpenAIModel(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "openai"


class OpenAIModelsResponse(BaseModel):
    object: str = "list"
    data: list[OpenAIModel]


# ---------- 自定义接口 ----------
class TTSSynthesizeRequest(BaseModel):
    text: str = Field(..., description="待合成文本")
    engine: str = Field(..., description="引擎名")
    voice_id: str | None = Field(None, description="已注册的自定义声音 id，用于复刻")
    voice: str | None = Field(None, description="预置说话人/音色名")
    format: str = Field("wav", description="输出格式")
    speed: float = Field(1.0, ge=0.25, le=4.0, description="语速")
    reference_audio_url: str | None = Field(None, description="公网 URL，用于即时音色克隆")


class EngineInfo(BaseModel):
    name: str
    description: str
    voices: list[str]
    supports_voice_clone: bool


class EnginesResponse(BaseModel):
    engines: list[EngineInfo]


class ModelInfo(BaseModel):
    id: str
    display_name: str | None = None
    engine: str
    path: str | None = None
    size_bytes: int = 0
    downloaded: bool = False
    downloaded_at: str | None = None


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class ModelDownloadRequest(BaseModel):
    model_id: str


class ModelClearRequest(BaseModel):
    model_id: str


# ---------- 自定义声音 ----------
class VoiceRegisterRequest(BaseModel):
    name: str = Field(..., description="自定义声音名")
    engine: str = Field(..., description="引擎名")
    description: str = Field("", description="可选描述")
    expire_days: int = Field(7, description="有效期天数：3/7/15/30/90/365/-1 永久")


class VoiceRecord(BaseModel):
    voice_id: str
    name: str
    engine: str
    description: str
    audio_path: str
    expire_days: int
    expires_at: str | None = None
    created_at: str


class VoicesResponse(BaseModel):
    voices: list[VoiceRecord]


class VoiceRegisterResponse(BaseModel):
    voice_id: str
    name: str
    engine: str
    description: str
    audio_path: str
    expire_days: int
    expires_at: str | None = None
    created_at: str


# ---------- 错误 ----------
class ErrorResponse(BaseModel):
    message: str
    code: str
    status: int

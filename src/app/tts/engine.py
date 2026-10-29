"""统一 TTS 引擎接口：对外暴露合成、声音复刻等能力。"""

from __future__ import annotations

from pathlib import Path

from app.tts.loader import LoadedModel, ModelLoader
from app.tts.manager import ModelManager
from app.tts.synthesizer import SynthesisResult, Synthesizer
from app.tts.voice_store import VoiceStore


class TTSEngine:
    """统一 TTS 接口。负责模型加载、声音复刻注册、文本合成。"""

    def __init__(self) -> None:
        self.loader = ModelLoader()
        self.synthesizer = Synthesizer(sample_rate=22050)
        self.voice_store = VoiceStore()
        self.loaded: dict[str, LoadedModel] = {}

    def load_model(self, model_id: str, local_path: Path) -> LoadedModel:
        """加载并缓存模型。"""
        if model_id in self.loaded:
            return self.loaded[model_id]
        loaded = self.loader.load(model_id, local_path)
        self.loaded[model_id] = loaded
        return loaded

    def get_loaded(self, model_id: str) -> LoadedModel | None:
        return self.loaded.get(model_id)

    def register_voice(
        self,
        name: str,
        engine: str,
        reference_audio_path: Path,
        *,
        description: str = "",
        expire_days: int = 7,
    ):
        """注册自定义声音（音色复刻），返回 voice_id。"""
        return self.voice_store.register_voice(
            name=name,
            engine=engine,
            reference_audio_path=reference_audio_path,
            description=description,
            expire_days=expire_days,
        )

    def list_voices(self):
        return self.voice_store.list_voices()

    def delete_voice(self, voice_id: str) -> bool:
        return self.voice_store.delete_voice(voice_id)

    def synthesize(
        self,
        text: str,
        model_id: str,
        *,
        voice_id: str | None = None,
        reference_audio: bytes | None = None,
        format: str = "wav",
        speed: float = 1.0,
    ) -> SynthesisResult:
        """合成语音。若未加载模型则先加载。"""
        loaded = self.loaded.get(model_id)
        if loaded is None:
            manager = ModelManager()
            model_path = manager.model_path(model_id)
            if model_path is None:
                raise FileNotFoundError(f"模型未下载: {model_id}")
            loaded = self.load_model(model_id, model_path)
        return self.synthesizer.synthesize(
            text=text,
            loaded=loaded,
            voice_id=voice_id,
            reference_audio=reference_audio,
            format=format,
            speed=speed,
        )

    def to_bytes(self, result: SynthesisResult) -> bytes:
        return self.synthesizer.to_bytes(result)

    def cleanup_expired_voices(self) -> int:
        return self.voice_store.cleanup_expired()

"""TTS 项目测试。"""

from __future__ import annotations

import sys
import types
import wave
from pathlib import Path

import numpy as np

from app.config import settings
from app.tts.manager import ModelManager
from app.tts.synthesizer import SynthesisResult, Synthesizer
from app.tts.voice_store import VoiceStore


def _make_wav(path: Path, seconds: float = 1.0, sr: int = 22050) -> None:
    n = int(sr * seconds)
    data = (np.sin(2 * np.pi * 440 * np.arange(n) / sr) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())


def test_settings_paths():
    assert settings.models_dir.name == "tts"
    assert settings.voices_dir.name == "voices"
    assert settings.device in ("cpu", "cuda")


def test_model_manager_list_empty(tmp_path):
    manager = ModelManager(models_dir=tmp_path / "tts")
    assert manager.list_models() == []


def test_voice_store_register_list_delete(tmp_path):
    store = VoiceStore(voices_dir=tmp_path / "voices")
    audio = tmp_path / "ref.wav"
    _make_wav(audio)

    record = store.register_voice(
        name="test_voice",
        engine="cosyvoice",
        reference_audio_path=audio,
        description="desc",
        expire_days=30,
    )
    assert record.voice_id
    assert record.name == "test_voice"
    assert record.engine == "cosyvoice"
    assert record.expire_days == 30
    assert record.audio_path.exists()

    voices = store.list_voices()
    assert len(voices) == 1
    assert voices[0].voice_id == record.voice_id

    got = store.get_voice(record.voice_id)
    assert got is not None
    assert got.voice_id == record.voice_id

    assert store.delete_voice(record.voice_id) is True
    assert store.get_voice(record.voice_id) is None
    assert store.delete_voice(record.voice_id) is False


def test_voice_store_permanent_expire_none(tmp_path):
    store = VoiceStore(voices_dir=tmp_path / "voices")
    audio = tmp_path / "ref.wav"
    _make_wav(audio)
    record = store.register_voice(
        name="perm",
        engine="cosyvoice",
        reference_audio_path=audio,
        expire_days=-1,
    )
    assert record.expire_days == -1
    assert record.expires_at is None


def test_synthesizer_to_bytes():
    synth = Synthesizer(sample_rate=8000)
    audio = np.zeros(8000, dtype=np.float32)
    res = SynthesisResult(audio=audio, sample_rate=8000, format="wav", duration_seconds=1.0)
    buf = synth.to_bytes(res)
    assert buf.startswith(b"RIFF")
    assert b"WAVE" in buf[:32]


class _FakeTensor:
    def cpu(self):
        return self

    def numpy(self):
        return np.zeros(100, dtype=np.float32)


class _FakeModel:
    def generate(self, **kwargs):
        return _FakeTensor()


class _FakeTokenizer:
    def __call__(self, text, return_tensors=None):
        return {"input_ids": [[1, 2, 3]]}


def test_synthesize_integration_monkeypatched(tmp_path):
    # 注入假 torch，避免依赖真实 transformers/torch
    torch_fake = types.ModuleType("torch")

    class _NoGrad:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    torch_fake.no_grad = lambda: _NoGrad()
    sys.modules["torch"] = torch_fake

    from app.tts.loader import LoadedModel

    loaded = LoadedModel(
        model_id="fake",
        local_path=tmp_path / "fake",
        model=_FakeModel(),
        tokenizer=_FakeTokenizer(),
        device="cpu",
    )
    synth = Synthesizer(sample_rate=8000)
    res = synth.synthesize(text="hi", loaded=loaded, format="wav", speed=1.0)
    assert isinstance(res.audio, np.ndarray)
    assert res.sample_rate == 8000
    assert res.duration_seconds >= 0

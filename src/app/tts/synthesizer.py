"""合成流水线：文本转音频推理，带进度条。"""

from __future__ import annotations

import io
import time
from dataclasses import dataclass

import numpy as np
from tqdm import tqdm

from app.tts.loader import LoadedModel


@dataclass
class SynthesisResult:
    audio: np.ndarray
    sample_rate: int
    format: str = "wav"
    duration_seconds: float = 0.0


class Synthesizer:
    """执行文本到音频推理，生成音频字节，全程显示进度条。"""

    def __init__(self, sample_rate: int = 22050) -> None:
        self.sample_rate = sample_rate

    def synthesize(
        self,
        text: str,
        loaded: LoadedModel,
        *,
        voice_id: str | None = None,
        reference_audio: bytes | None = None,
        format: str = "wav",
        speed: float = 1.0,
    ) -> SynthesisResult:
        """合成语音。返回音频数组与元数据。"""
        steps = [
            ("文本编码", self.encode_text),
            ("音频生成", self.generate_audio),
            ("后处理", self.post_process),
        ]

        ctx: dict = {
            "text": text,
            "loaded": loaded,
            "voice_id": voice_id,
            "reference_audio": reference_audio,
            "speed": speed,
            "tokens": None,
            "audio": None,
        }

        with tqdm(total=len(steps), desc=f"合成语音 ({format})", unit="step") as pbar:
            for name, fn in steps:
                pbar.set_description(f"合成语音 - {name}")
                fn(ctx)
                pbar.update(1)
                time.sleep(0.05)

        audio: np.ndarray = ctx["audio"]
        duration = float(len(audio)) / float(self.sample_rate)

        return SynthesisResult(
            audio=audio,
            sample_rate=self.sample_rate,
            format=format,
            duration_seconds=duration,
        )

    def to_bytes(self, result: SynthesisResult) -> bytes:
        """将合成结果写入 WAV 字节流。"""
        import wave

        buf = io.BytesIO()
        audio = result.audio
        if audio.dtype != np.int16:
            audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(result.sample_rate)
            wf.writeframes(audio.tobytes())
        return buf.getvalue()

    def encode_text(self, ctx: dict) -> None:
        tokenizer = ctx["loaded"].tokenizer
        ctx["tokens"] = tokenizer(ctx["text"], return_tensors="pt")

    def generate_audio(self, ctx: dict) -> None:
        import torch

        model = ctx["loaded"].model
        tokens = ctx["tokens"]
        with torch.no_grad():
            outputs = model.generate(**tokens, max_new_tokens=256)
        ctx["audio"] = outputs.cpu().numpy().astype(np.float32) / 32768.0

    def post_process(self, ctx: dict) -> None:
        audio = ctx["audio"]
        speed = ctx["speed"]
        if speed != 1.0:
            idx = np.linspace(0, len(audio) - 1, int(len(audio) / speed))
            audio = np.interp(idx, np.arange(len(audio)), audio)
        ctx["audio"] = audio

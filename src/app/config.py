"""项目配置：路径、设备、默认参数。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
MODELS_DIR: Path = PROJECT_ROOT / "models"
TTS_MODELS_DIR: Path = MODELS_DIR / "tts"
VOICES_DIR: Path = MODELS_DIR / "voices"

DEFAULT_DEVICE: str = "cuda" if os.environ.get("USE_CUDA", "0") == "1" else "cpu"
DEFAULT_MAX_NEW_TOKENS: int = 256
DEFAULT_SAMPLE_RATE: int = 22050


@dataclass(frozen=True)
class Settings:
    models_dir: Path = TTS_MODELS_DIR
    voices_dir: Path = VOICES_DIR
    device: str = DEFAULT_DEVICE
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS
    sample_rate: int = DEFAULT_SAMPLE_RATE


settings = Settings()

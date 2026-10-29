"""模型管理：通过 huggingface_hub 下载/列出/清理模型，带进度条。"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download
from tqdm import tqdm

from app.config import TTS_MODELS_DIR


@dataclass
class ModelInfo:
    model_id: str
    engine: str
    local_path: Path
    size_bytes: int


class ModelManager:
    """负责 TTS 模型的下载、列表与清理。"""

    def __init__(self, models_dir: Path = TTS_MODELS_DIR) -> None:
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def model_dir(self, model_id: str) -> Path:
        safe = model_id.replace("/", "__")
        return self.models_dir / safe

    def list_models(self) -> list[ModelInfo]:
        """列出本地已下载的模型。"""
        infos: list[ModelInfo] = []
        if not self.models_dir.exists():
            return infos
        for entry in sorted(self.models_dir.iterdir()):
            if entry.is_dir():
                size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
                parts = entry.name.split("__", 1)
                engine = parts[0] if len(parts) > 1 else "unknown"
                model_id = parts[1] if len(parts) > 1 else entry.name
                infos.append(
                    ModelInfo(
                        model_id=model_id,
                        engine=engine,
                        local_path=entry,
                        size_bytes=size,
                    )
                )
        return infos

    def download_model(
        self,
        repo_id: str,
        engine: str = "auto",
        *,
        force_download: bool = False,
    ) -> Path:
        """通过 huggingface_hub 下载模型到 models/tts/<engine>__<repo_id>，显示进度条。"""
        target_dir = self.model_dir(repo_id) if engine == "auto" else self.models_dir / f"{engine}__{repo_id}"
        target_dir.mkdir(parents=True, exist_ok=True)

        with tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"下载模型 {repo_id}",
            leave=False,
        ) as pbar:

            def progress(current: int, total: int) -> None:
                pbar.total = total
                pbar.n = current
                pbar.refresh()

            snapshot_download(
                repo_id=repo_id,
                local_dir=str(target_dir),
                force_download=force_download,
                local_dir_use_symlinks=False,
            )

        return target_dir

    def download_file(
        self,
        repo_id: str,
        filename: str,
        engine: str = "auto",
    ) -> Path:
        """下载单个模型文件，显示进度条。"""
        target_dir = self.model_dir(repo_id) if engine == "auto" else self.models_dir / f"{engine}__{repo_id}"
        target_dir.mkdir(parents=True, exist_ok=True)

        with tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"下载文件 {filename}",
            leave=False,
        ) as pbar:

            def progress(current: int, total: int) -> None:
                pbar.total = total
                pbar.n = current
                pbar.refresh()

            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(target_dir),
                local_dir_use_symlinks=False,
            )

        return target_dir / filename

    def clear_model(self, model_id: str) -> bool:
        """删除本地模型目录。"""
        target_dir = self.model_dir(model_id)
        if target_dir.exists():
            shutil.rmtree(target_dir)
            return True
        return False

    def model_path(self, model_id: str) -> Path | None:
        target_dir = self.model_dir(model_id)
        return target_dir if target_dir.exists() else None

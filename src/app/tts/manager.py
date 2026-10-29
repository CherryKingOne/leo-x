"""模型管理：通过 huggingface_hub 下载/列出/清理模型，带进度条。

所有模型直接扁平存放在 models/tts/<model_id>/ 目录下，不再按 engine 分目录。
内置模型映射表由 models/tts/models.json 管理：
  {"models": {"voxcpm-2.0": {"display_name": "voxcpm-2.0", "hf_repo_id": "openbmb/VoxCPM2"}}}
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download
from tqdm import tqdm

from app.config import TTS_MODELS_DIR


@dataclass
class ModelEntry:
    model_id: str
    display_name: str
    hf_repo_id: str
    downloaded: bool = False
    local_path: Path | None = None
    size_bytes: int = 0


@dataclass
class ModelInfo:
    model_id: str
    local_path: Path
    size_bytes: int


class ModelManager:
    """负责 TTS 模型的下载、列表与清理。

    模型映射表由 models/tts/models.json 管理，对外展示名称为
    display_name（如 voxcpm-2.0 / indextts-2.5），实际从 HF 下载时使用
    对应的 hf_repo_id。所有模型直接下载到 models/tts/<model_id>/。
    """

    def __init__(self, models_dir: Path = TTS_MODELS_DIR) -> None:
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.mapping_file = self.models_dir / "models.json"
        self._mapping: dict[str, ModelEntry] = {}
        self._load_mapping()

    def _load_mapping(self) -> None:
        if not self.mapping_file.exists():
            return
        try:
            data = json.loads(self.mapping_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        for model_id, entry in data.get("models", {}).items():
            self._mapping[model_id] = ModelEntry(
                model_id=model_id,
                display_name=entry.get("display_name", model_id),
                hf_repo_id=entry["hf_repo_id"],
            )

    def get_mapping(self) -> dict[str, ModelEntry]:
        return dict(self._mapping)

    def resolve_repo_id(self, model_id: str) -> str:
        """将 display_name / model_id 解析为 HF repo_id。不存在则原样返回。"""
        entry = self._mapping.get(model_id)
        if entry is not None:
            return entry.hf_repo_id
        return model_id

    def resolve_display_name(self, model_id: str) -> str:
        entry = self._mapping.get(model_id)
        if entry is not None:
            return entry.display_name
        return model_id

    def local_dir_for(self, model_id: str) -> Path:
        return self.models_dir / model_id

    def list_models(self) -> list[ModelEntry]:
        """列出所有已注册模型，标注是否已下载。已下载的排在前面。"""
        entries: list[ModelEntry] = []
        for model_id, entry in self._mapping.items():
            local_dir = self.local_dir_for(model_id)
            if local_dir.exists() and any(local_dir.iterdir()):
                size = sum(f.stat().st_size for f in local_dir.rglob("*") if f.is_file())
                entries.append(
                    ModelEntry(
                        model_id=entry.model_id,
                        display_name=entry.display_name,
                        hf_repo_id=entry.hf_repo_id,
                        downloaded=True,
                        local_path=local_dir,
                        size_bytes=size,
                    )
                )
            else:
                entries.append(
                    ModelEntry(
                        model_id=entry.model_id,
                        display_name=entry.display_name,
                        hf_repo_id=entry.hf_repo_id,
                        downloaded=False,
                        local_path=None,
                        size_bytes=0,
                    )
                )
        # 扫描映射表之外的本地目录
        known_dirs = {self.local_dir_for(mid) for mid in self._mapping}
        if self.models_dir.exists():
            for entry_path in sorted(self.models_dir.iterdir()):
                if entry_path.is_dir() and entry_path not in known_dirs:
                    size = sum(f.stat().st_size for f in entry_path.rglob("*") if f.is_file())
                    entries.append(
                        ModelEntry(
                            model_id=entry_path.name,
                            display_name=entry_path.name,
                            hf_repo_id="",
                            downloaded=True,
                            local_path=entry_path,
                            size_bytes=size,
                        )
                    )
        entries.sort(key=lambda e: (not e.downloaded, e.model_id))
        return entries

    def download_model(
        self,
        model_id: str,
        *,
        force_download: bool = False,
    ) -> Path:
        """通过 huggingface_hub 下载模型到 models/tts/<model_id>/，显示进度条。

        model_id 可以是 display_name（如 voxcpm-2.0），会自动映射到 HF repo_id。
        """
        repo_id = self.resolve_repo_id(model_id)
        target_dir = self.local_dir_for(model_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        with tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"下载模型 {model_id} ({repo_id})",
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
        model_id: str,
        filename: str,
    ) -> Path:
        """下载单个模型文件，显示进度条。"""
        repo_id = self.resolve_repo_id(model_id)
        target_dir = self.local_dir_for(model_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        with tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"下载文件 {filename} ({repo_id})",
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
        target_dir = self.local_dir_for(model_id)
        if target_dir.exists():
            shutil.rmtree(target_dir)
            return True
        return False

    def model_path(self, model_id: str) -> Path | None:
        target_dir = self.local_dir_for(model_id)
        return target_dir if target_dir.exists() else None

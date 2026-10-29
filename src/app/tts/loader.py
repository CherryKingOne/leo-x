"""模型加载：通过 transformers 实例化模型与分词器，带进度条。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from tqdm import tqdm
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer

from app.config import settings


@dataclass
class LoadedModel:
    model_id: str
    local_path: Path
    model: object
    tokenizer: object
    device: str


class ModelLoader:
    """负责通过 transformers 加载模型与分词器，全程显示进度条。"""

    def __init__(self, device: str | None = None) -> None:
        self.device = device or settings.device

    def load(self, model_id: str, local_path: Path) -> LoadedModel:
        """加载模型与分词器，显示加载进度条。"""
        steps = [
            ("检查模型文件", self.check_files),
            ("加载分词器", self.load_tokenizer),
            ("加载模型权重", self.load_model_weights),
            ("移至设备", self.move_to_device),
        ]

        ctx: dict = {"local_path": local_path, "model_id": model_id, "tokenizer": None, "model": None}

        with tqdm(total=len(steps), desc=f"加载模型 {model_id}", unit="step") as pbar:
            for name, fn in steps:
                pbar.set_description(f"加载模型 {model_id} - {name}")
                fn(ctx)
                pbar.update(1)
                time.sleep(0.05)

        return LoadedModel(
            model_id=model_id,
            local_path=local_path,
            model=ctx["model"],
            tokenizer=ctx["tokenizer"],
            device=self.device,
        )

    def check_files(self, ctx: dict) -> None:
        local_path: Path = ctx["local_path"]
        if not local_path.exists():
            raise FileNotFoundError(f"模型目录不存在: {local_path}")
        if not any(local_path.iterdir()):
            raise FileNotFoundError(f"模型目录为空: {local_path}")

    def load_tokenizer(self, ctx: dict) -> None:
        ctx["tokenizer"] = AutoTokenizer.from_pretrained(str(ctx["local_path"]))

    def load_model_weights(self, ctx: dict) -> None:
        local_path = ctx["local_path"]
        try:
            ctx["model"] = AutoModelForCausalLM.from_pretrained(str(local_path))
        except Exception:
            ctx["model"] = AutoModel.from_pretrained(str(local_path))

    def move_to_device(self, ctx: dict) -> None:
        if self.device != "cpu":
            try:
                ctx["model"].to(self.device)
            except Exception:
                pass

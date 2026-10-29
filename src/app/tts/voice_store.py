"""自定义声音注册/存储：voice_id 生成、有效期管理、到期清理，带进度条。"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from tqdm import tqdm

from app.config import settings


@dataclass
class VoiceRecord:
    voice_id: str
    name: str
    engine: str
    description: str
    audio_path: Path
    expire_days: int
    expires_at: str | None
    created_at: str


class VoiceStore:
    """管理自定义声音（音色复刻）的注册、查询、删除与过期清理。"""

    def __init__(self, voices_dir: Path = settings.voices_dir) -> None:
        self.voices_dir = voices_dir
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.voices_dir / "index.json"

    def load_index(self) -> dict:
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def save_index(self, index: dict) -> None:
        self.index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    def generate_voice_id(self, name: str, engine: str) -> str:
        raw = f"{name}:{engine}:{uuid4().hex}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def register_voice(
        self,
        name: str,
        engine: str,
        reference_audio_path: Path,
        *,
        description: str = "",
        expire_days: int = 7,
    ) -> VoiceRecord:
        """注册自定义声音。复制参考音频到 models/voices/<voice_id>/ref.wav，返回 voice_id。"""
        voice_id = self.generate_voice_id(name, engine)
        voice_dir = self.voices_dir / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        dest_audio = voice_dir / "ref.wav"
        with tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"复制参考音频 -> {voice_id}",
            leave=False,
        ) as pbar:
            total = reference_audio_path.stat().st_size
            pbar.total = total
            copied = 0
            with reference_audio_path.open("rb") as src, dest_audio.open("wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied += len(chunk)
                    pbar.n = copied
                    pbar.refresh()
            time.sleep(0.05)

        now = datetime.now(UTC)
        expires_at: str | None = None
        if expire_days != -1:
            expires_at = (now + timedelta(days=expire_days)).isoformat()

        record = VoiceRecord(
            voice_id=voice_id,
            name=name,
            engine=engine,
            description=description,
            audio_path=dest_audio,
            expire_days=expire_days,
            expires_at=expires_at,
            created_at=now.isoformat(),
        )

        index = self.load_index()
        index[voice_id] = {
            "voice_id": record.voice_id,
            "name": record.name,
            "engine": record.engine,
            "description": record.description,
            "audio_path": str(record.audio_path),
            "expire_days": record.expire_days,
            "expires_at": record.expires_at,
            "created_at": record.created_at,
        }
        self.save_index(index)

        return record

    def list_voices(self) -> list[VoiceRecord]:
        """列出所有自定义声音。"""
        index = self.load_index()
        records: list[VoiceRecord] = []
        for data in index.values():
            records.append(
                VoiceRecord(
                    voice_id=data["voice_id"],
                    name=data["name"],
                    engine=data["engine"],
                    description=data.get("description", ""),
                    audio_path=Path(data["audio_path"]),
                    expire_days=data.get("expire_days", 7),
                    expires_at=data.get("expires_at"),
                    created_at=data.get("created_at", ""),
                )
            )
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records

    def get_voice(self, voice_id: str) -> VoiceRecord | None:
        index = self.load_index()
        data = index.get(voice_id)
        if not data:
            return None
        return VoiceRecord(
            voice_id=data["voice_id"],
            name=data["name"],
            engine=data["engine"],
            description=data.get("description", ""),
            audio_path=Path(data["audio_path"]),
            expire_days=data.get("expire_days", 7),
            expires_at=data.get("expires_at"),
            created_at=data.get("created_at", ""),
        )

    def delete_voice(self, voice_id: str) -> bool:
        """删除自定义声音及其参考音频。"""
        index = self.load_index()
        data = index.pop(voice_id, None)
        if data is None:
            return False
        audio_path = Path(data.get("audio_path", ""))
        if audio_path.exists() and audio_path.parent == self.voices_dir / voice_id:
            shutil.rmtree(self.voices_dir / voice_id, ignore_errors=True)
        self.save_index(index)
        return True

    def cleanup_expired(self) -> int:
        """删除已过期的非永久声音，返回删除数量。"""
        now = datetime.now(UTC)
        removed = 0
        for record in self.list_voices():
            if record.expire_days == -1 or record.expires_at is None:
                continue
            try:
                expires_at = datetime.fromisoformat(record.expires_at)
            except ValueError:
                continue
            if now >= expires_at:
                self.delete_voice(record.voice_id)
                removed += 1
        return removed

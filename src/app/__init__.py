"""TTS 服务包入口。"""

from __future__ import annotations

from app.cli import cli_app


def main() -> None:
    """CLI 入口点。"""
    cli_app()

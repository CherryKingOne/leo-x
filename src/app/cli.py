"""CLI 入口：typer 命令行，支持启动服务、模型下载、合成等。"""

from __future__ import annotations

from pathlib import Path

import typer

from app.tts.engine import TTSEngine
from app.tts.manager import ModelManager

cli_app = typer.Typer(add_completion=False, help="TTS 服务命令行工具")


@cli_app.command()
def server(
    host: str = typer.Option("0.0.0.0", help="监听地址"),
    port: int = typer.Option(8000, help="监听端口"),
):
    """启动 FastAPI HTTP 服务。"""
    import uvicorn

    from app.api import app as fastapi_app

    uvicorn.run(fastapi_app, host=host, port=port)


@cli_app.command()
def download(model_id: str, engine: str = "auto"):
    """通过 huggingface_hub 下载模型（带进度条）。"""
    manager = ModelManager()
    path = manager.download_model(repo_id=model_id, engine=engine)
    typer.echo(f"已下载: {path}")


@cli_app.command()
def list_models():
    """列出已下载模型。"""
    manager = ModelManager()
    infos = manager.list_models()
    if not infos:
        typer.echo("暂无已下载模型。")
        return
    for m in infos:
        typer.echo(f"{m.model_id} | engine={m.engine} | {m.size_bytes} 字节 | {m.local_path}")


@cli_app.command()
def clear_model(model_id: str):
    """清理模型缓存。"""
    manager = ModelManager()
    if manager.clear_model(model_id):
        typer.echo(f"已清理: {model_id}")
    else:
        typer.echo(f"未找到: {model_id}")


@cli_app.command()
def register_voice(
    name: str,
    engine: str,
    reference_audio: Path,
    description: str = "",
    expire_days: int = 7,
):
    """注册自定义声音（音色复刻），返回 voice_id。"""
    tts = TTSEngine()
    record = tts.register_voice(
        name=name,
        engine=engine,
        reference_audio_path=reference_audio,
        description=description,
        expire_days=expire_days,
    )
    typer.echo(f"voice_id={record.voice_id}")
    typer.echo(f"name={record.name} engine={record.engine}")
    typer.echo(f"expire_days={record.expire_days} expires_at={record.expires_at}")


@cli_app.command()
def list_voices():
    """列出自定义声音。"""
    tts = TTSEngine()
    records = tts.list_voices()
    if not records:
        typer.echo("暂无自定义声音。")
        return
    for r in records:
        typer.echo(
            f"{r.voice_id} | {r.name} | engine={r.engine} | expire={r.expire_days} | {r.created_at}"
        )


@cli_app.command()
def delete_voice(voice_id: str):
    """删除自定义声音。"""
    tts = TTSEngine()
    if tts.delete_voice(voice_id):
        typer.echo(f"已删除: {voice_id}")
    else:
        typer.echo(f"未找到: {voice_id}")


@cli_app.command()
def synthesize(
    text: str,
    model_id: str,
    output: Path = typer.Option(Path("output.wav"), help="输出音频路径"),  # noqa: B008
    voice_id: str | None = typer.Option(None, help="自定义声音 id"),
    format: str = typer.Option("wav", help="输出格式"),
    speed: float = typer.Option(1.0, help="语速"),
):
    """文本合成并保存音频文件。"""
    tts = TTSEngine()
    result = tts.synthesize(
        text=text,
        model_id=model_id,
        voice_id=voice_id,
        format=format,
        speed=speed,
    )
    output.write_bytes(tts.to_bytes(result))
    typer.echo(f"已合成: {output} (时长 {result.duration_seconds:.2f}s)")


if __name__ == "__main__":
    cli_app()

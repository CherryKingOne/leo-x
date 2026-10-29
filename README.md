# leo-x

基于 Python 3.12 + uv 的 TTS（文本转语音）服务，提供 OpenAI 兼容接口与自定义接口，支持模型下载/加载/合成、自定义声音（音色复刻）注册与复用，全流程进度条。

## 快速开始

### 1. 环境准备

确保已安装 [uv](https://github.com/astral-sh/uv) 与 Python 3.12：

```bash
# 检查 uv
uv --version
# 检查 Python
python3 --version
```

### 2. 克隆并安装依赖

```bash
git clone https://github.com/CherryKingOne/leo-x.git
cd leo-x

# 创建虚拟环境并安装依赖（Python 3.12）
uv sync
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

### 3. 启动服务

启动 FastAPI HTTP 服务（默认 `http://0.0.0.0:8000`）：

```bash
# 方式 A：通过 uv run
uv run app server

# 方式 B：直接用 cli 入口
uv run app server --host 0.0.0.0 --port 8000
```

服务启动后：
- API 文档：`http://localhost:8000/docs`
- OpenAPI 规范：`http://localhost:8000/openapi.json`

### 4. 常用 CLI 命令

所有命令均在 `.venv` 激活后或通过 `uv run app <命令>` 使用。

| 命令 | 说明 | 示例 |
|------|------|------|
| `app server` | 启动 HTTP 服务 | `uv run app server --port 8000` |
| `app download` | 从 huggingface_hub 下载模型（进度条） | `uv run app download voxcpm-2.0` |
| `app list-models` | 列出已下载模型 | `uv run app list-models` |
| `app clear-model` | 清理模型缓存 | `uv run app clear-model tts-1` |
| `app register-voice` | 注册自定义声音（音色复刻），返回 voice_id | `uv run app register-voice myvoice cosyvoice ref.wav --expire-days 30` |
| `app list-voices` | 列出自定义声音 | `uv run app list-voices` |
| `app delete-voice` | 删除自定义声音 | `uv run app delete-voice <voice_id>` |
| `app synthesize` | 文本合成并保存音频 | `uv run app synthesize "你好" tts-1 --output out.wav` |

### 5. 接口调用示例

#### OpenAI 兼容接口

```bash
# 文本转语音
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"你好，世界","voice":"alloy","response_format":"mp3","speed":1.0}' \
  --output output.mp3

# 列出模型
curl http://localhost:8000/v1/models
```

#### 自定义接口

```bash
# 文本合成（URL 音色克隆）
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","engine":"voxcpm-2.0","reference_audio_url":"https://example.com/ref.wav","format":"wav"}' \
  --output output.wav

# 上传参考音频合成
curl -X POST http://localhost:8000/api/v1/tts/synthesize-upload \
  -F "text=你好" \
  -F "engine=cosyvoice" \
  -F "reference_audio=@ref.wav" \
  --output output.wav

# 注册自定义声音（返回 voice_id，后续直接用 id 复刻）
curl -X POST http://localhost:8000/api/v1/tts/voices \
  -F "name=myvoice" \
  -F "engine=voxcpm-2.0" \
  -F "reference_audio=@ref.wav" \
  -F "expire_days=30"

# 列出自定义声音
curl http://localhost:8000/api/v1/tts/voices

# 删除自定义声音
curl -X DELETE http://localhost:8000/api/v1/tts/voices/<voice_id>
```

### 6. 运行测试

```bash
uv run pytest tests/ -v
```

### 7. 目录结构

```
models/tts/          # TTS 模型本地存放
models/voices/       # 自定义声音参考音频
src/app/
  tts/manager.py     # huggingface_hub 模型下载（进度条）
  tts/loader.py      # transformers 模型加载（进度条）
  tts/synthesizer.py # 文本转音频合成（进度条）
  tts/voice_store.py # 自定义声音注册/复刻（进度条）
  tts/engine.py      # 统一 TTS 引擎接口
  api/               # OpenAI 兼容 + 自定义 HTTP 接口
  cli.py             # typer 命令行入口
tests/               # 单元测试
```

## 代码规范

详见 `.claude/rules/code-style.md`：
- 全部使用绝对路径导入（禁止 `..` / `.` 相对导入）
- 禁止下划线开头的函数/方法/类名（双下划线魔术方法豁免）

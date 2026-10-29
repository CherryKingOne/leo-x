# API 接口协议设计

两套接口共用同一套底层引擎，仅协议格式不同。

---

## 一、OpenAI 兼容接口

完全对齐 OpenAI 官方 TTS 接口格式，方便直接替换/对接现有 OpenAI 客户端。

### `POST /v1/audio/speech` — 文本转语音

**Request Body** (`application/json`):
```json
{
  "model": "tts-1",
  "input": "Hello, how are you?",
  "voice": "alloy",
  "response_format": "mp3",
  "speed": 1.0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | 模型名（对应本地已下载模型） |
| input | string | 是 | 待合成文本 |
| voice | string | 否 | 说话人/音色标识 |
| response_format | string | 否 | `mp3` / `wav` / `ogg` / `flac` / `pcm`，默认 `mp3` |
| speed | float | 否 | 语速，0.25~4.0，默认 1.0 |

**Response**: `application/octet-stream`，直接返回音频二进制流。

### `GET /v1/models` — 列出可用模型

**Response** (`application/json`):
```json
{
  "object": "list",
  "data": [
    {
      "id": "tts-1",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    }
  ]
}
```

---

## 二、自定义接口

功能更丰富，支持文件上传、公网 URL、多引擎、模型管理。

### `POST /api/v1/tts/synthesize` — 文本合成（URL 克隆音色）

**Request Body** (`application/json`):
```json
{
  "text": "Hello world",
  "engine": "cosyvoice",
  "voice": "alice",
  "format": "mp3",
  "speed": 1.0,
  "reference_audio_url": "https://example.com/ref.wav"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待合成文本 |
| engine | string | 是 | 引擎名（cosyvoice / fishspeech / ...） |
| voice | string | 否 | 说话人 |
| format | string | 否 | 输出格式，默认 `wav` |
| speed | float | 否 | 语速 |
| reference_audio_url | string | 否 | 公网 URL，用于音色克隆 |

**Response**: `application/octet-stream`，音频二进制流。

### `POST /api/v1/tts/synthesize-upload` — 文本合成（上传音色文件）

**Request** (`multipart/form-data`):
```
text: "Hello world"
engine: "cosyvoice"
voice: "alice"
format: "mp3"
speed: 1.0
reference_audio: <file>          # 音频文件
```

**Response**: `application/octet-stream`，音频二进制流。

### `GET /api/v1/tts/engines` — 列出可用引擎

**Response**:
```json
{
  "engines": [
    {
      "name": "cosyvoice",
      "description": "CosyVoice TTS",
      "voices": ["alice", "bob"],
      "supports_voice_clone": true
    }
  ]
}
```

### `GET /api/v1/tts/models` — 列出已下载模型

**Response**:
```json
{
  "models": [
    {
      "id": "tts-1",
      "engine": "cosyvoice",
      "path": "/workspace/app/models/tts/cosyvoice",
      "size_bytes": 1234567890,
      "downloaded_at": "2026-10-29T07:00:00Z"
    }
  ]
}
```

### `POST /api/v1/tts/models/download` — 下载模型

**Request**:
```json
{
  "model_id": "cosyvoice",
  "engine": "cosyvoice"
}
```

### `POST /api/v1/tts/models/clear` — 清理模型缓存

**Request**:
```json
{
  "model_id": "cosyvoice"
}
```

---

## 三、两套接口对应关系

| 能力 | OpenAI 兼容 | 自定义 |
|------|------------|--------|
| 文本合成 | `/v1/audio/speech` | `/api/v1/tts/synthesize` |
| 文件上传音色 | ❌ 不支持 | `/api/v1/tts/synthesize-upload` |
| URL 克隆音色 | ❌ 不支持 | `/api/v1/tts/synthesize` (+ `reference_audio_url`) |
| 多引擎切换 | 仅 model 字段 | `engine` 字段显式指定 |
| 模型管理 | `/v1/models`（只读） | `/api/v1/tts/models` + 下载/清理 |
| 引擎列表 | ❌ | `/api/v1/tts/engines` |
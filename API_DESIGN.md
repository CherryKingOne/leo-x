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
| voice | string | 否 | 说话人；可为预置音色名，或已注册的自定义声音名（通过 `/api/v1/tts/voices` 注册） |
| format | string | 否 | 输出格式，默认 `wav` |
| speed | float | 否 | 语速 |
| reference_audio_url | string | 否 | 公网 URL，用于音色克隆（与 voice 二选一，优先级高于 voice） |

**Response**: `application/octet-stream`，音频二进制流。

### `POST /api/v1/tts/synthesize-upload` — 文本合成（上传音色文件）

**Request** (`multipart/form-data`):
```
text: "Hello world"
engine: "cosyvoice"
voice: "alice"                  # 可为预置音色，或已注册的自定义声音名
format: "mp3"
speed: 1.0
reference_audio: <file>          # 音频文件，用于音色克隆
```

**Response**: `application/octet-stream`，音频二进制流。

### `POST /api/v1/tts/voices` — 注册自定义声音（音色复刻）

**Request** (`multipart/form-data`):
```
name: "my_voice"             # 自定义声音名，必填
engine: "cosyvoice"          # 引擎名，必填
description: "My custom voice"  # 可选描述
reference_audio: <file>      # 用于音色复刻的音频文件，必填
```

**Response** (`application/json`):
```json
{
  "name": "my_voice",
  "engine": "cosyvoice",
  "description": "My custom voice",
  "audio_path": "/workspace/app/models/tts/voices/my_voice/ref.wav",
  "created_at": "2026-10-29T07:15:00Z"
}
```

### `GET /api/v1/tts/voices` — 列出自定义声音

**Response** (`application/json`):
```json
{
  "voices": [
    {
      "name": "my_voice",
      "engine": "cosyvoice",
      "description": "My custom voice",
      "audio_path": "/workspace/app/models/tts/voices/my_voice/ref.wav",
      "created_at": "2026-10-29T07:15:00Z"
    }
  ]
}
```

### `DELETE /api/v1/tts/voices/{name}` — 删除自定义声音

**Response**: `204 No Content`

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
| 预置音色 | `voice` 字段 | `voice` 字段 |
| 文件上传音色 | ❌ 不支持 | `/api/v1/tts/synthesize-upload` |
| URL 克隆音色 | ❌ 不支持 | `/api/v1/tts/synthesize` (+ `reference_audio_url`) |
| **自定义声音注册/复刻** | ❌ 不支持 | `/api/v1/tts/voices`（注册、列表、删除） |
| 多引擎切换 | 仅 model 字段 | `engine` 字段显式指定 |
| 模型管理 | `/v1/models`（只读） | `/api/v1/tts/models` + 下载/清理 |
| 引擎列表 | ❌ | `/api/v1/tts/engines` |

## 四、音色复刻能力说明

自定义声音（音色复刻）是自定义接口的专属能力，OpenAI 兼容接口不支持。

**流程**：
1. 上传参考音频 → `POST /api/v1/tts/voices` 注册为具名声音
2. 后续合成时，`voice` 字段传入该声音名即可复刻
3. 也可在单次合成时直接传 `reference_audio` / `reference_audio_url`，无需预先注册

**三种使用方式**（优先级从高到低）：
1. `reference_audio`（上传文件）或 `reference_audio_url`（公网 URL）— 即时克隆，不注册
2. `voice` = 已注册的自定义声音名 — 使用已复刻的声音
3. `voice` = 引擎预置音色名 — 使用预置声音
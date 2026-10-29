# 自定义接口文档

自定义 TTS 接口，功能丰富，支持文件上传、公网 URL、多引擎、模型管理、自定义声音（音色复刻）等基础操作。

## 基础信息

- **Base URL**：`http://<host>:<port>`
- **Content-Type**：`application/json` 或 `multipart/form-data`
- **鉴权**：暂不支持（后续可加 API Key）

---

## 一、文本合成接口

### 1. `POST /api/v1/tts/synthesize` — 文本合成（支持 URL 音色克隆）

使用 JSON 请求体合成语音，支持通过公网 URL 提供参考音频进行音色克隆。

**请求方式**：`POST`
**Content-Type**：`application/json`

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| text | string | 是 | — | 待合成文本 |
| engine | string | 是 | — | 引擎名（如 `cosyvoice`、`fishspeech`） |
| voice_id | string | 否 | — | 已注册的自定义声音 ID（通过 `/api/v1/tts/voices` 注册返回），用于复刻 |
| voice | string | 否 | — | 预置说话人/音色名（如 `alice`） |
| format | string | 否 | `wav` | 输出格式：`wav` / `mp3` / `ogg` / `flac` |
| speed | float | 否 | 1.0 | 语速 |
| reference_audio_url | string | 否 | — | 公网 URL，用于即时音色克隆，优先级高于 voice_id |

#### 优先级

`reference_audio_url` > `voice_id` > `voice`

#### 请求示例

```json
{
  "text": "Hello world",
  "engine": "cosyvoice",
  "voice_id": "a1b2c3d4e5f67890",
  "format": "mp3",
  "speed": 1.0
}
```

#### 响应

**成功**：`200 OK`
- **Content-Type**：`application/octet-stream`
- **Body**：音频二进制流

#### curl 示例（URL 克隆）

```bash
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "engine": "cosyvoice",
    "reference_audio_url": "https://example.com/ref.wav",
    "format": "mp3"
  }' \
  --output output.mp3
```

---

### 2. `POST /api/v1/tts/synthesize-upload` — 文本合成（上传音色文件）

使用 multipart/form-data 合成语音，支持上传参考音频文件进行音色克隆。

**请求方式**：`POST`
**Content-Type**：`multipart/form-data`

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| text | string | 是 | — | 待合成文本 |
| engine | string | 是 | — | 引擎名 |
| voice_id | string | 否 | — | 已注册的自定义声音 ID，用于复刻 |
| voice | string | 否 | — | 预置说话人/音色名 |
| format | string | 否 | `wav` | 输出格式 |
| speed | float | 否 | 1.0 | 语速 |
| reference_audio | file | 否 | — | 参考音频文件，用于即时音色克隆 |

#### 优先级

`reference_audio` > `voice_id` > `voice`

#### 请求示例

```http
POST /api/v1/tts/synthesize-upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="text"

Hello world
------WebKitFormBoundary
Content-Disposition: form-data; name="engine"

cosyvoice
------WebKitFormBoundary
Content-Disposition: form-data; name="reference_audio"; filename="ref.wav"
Content-Type: audio/wav

<二进制文件内容>
------WebKitFormBoundary--
```

#### 响应

**成功**：`200 OK`
- **Content-Type**：`application/octet-stream`
- **Body**：音频二进制流

#### curl 示例（上传文件）

```bash
curl -X POST http://localhost:8000/api/v1/tts/synthesize-upload \
  -F "text=Hello world" \
  -F "engine=cosyvoice" \
  -F "reference_audio=@/path/to/ref.wav" \
  -F "format=mp3" \
  --output output.mp3
```

---

## 二、自定义声音（音色复刻）接口

创建一次自定义声音后，后续复刻直接使用 `voice_id`，无需重复上传参考音频。

### 3. `POST /api/v1/tts/voices` — 注册自定义声音

上传参考音频，注册为具名自定义声音，返回 `voice_id`。

**请求方式**：`POST`
**Content-Type**：`multipart/form-data`

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| name | string | 是 | — | 自定义声音名 |
| engine | string | 是 | — | 引擎名 |
| description | string | 否 | — | 可选描述 |
| reference_audio | file | 是 | — | 用于音色复刻的音频文件 |
| expire_days | int | 否 | 7 | 有效期（天）：3 / 7 / 15 / 30 / 90 / 365 / -1（永久） |

#### 请求示例

```http
POST /api/v1/tts/voices
Content-Type: multipart/form-data

name: my_voice
engine: cosyvoice
description: My custom voice
reference_audio: <file>
expire_days: 30
```

#### 响应示例

```json
{
  "voice_id": "a1b2c3d4e5f67890",
  "name": "my_voice",
  "engine": "cosyvoice",
  "description": "My custom voice",
  "audio_path": "/workspace/app/models/voices/a1b2c3d4e5f67890/ref.wav",
  "expire_days": 30,
  "expires_at": "2026-11-28T07:19:21Z",
  "created_at": "2026-10-29T07:19:21Z"
}
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| voice_id | string | 声音唯一标识（UUID 转哈希值），后续复刻用此 id |
| name | string | 自定义声音名 |
| engine | string | 引擎名 |
| description | string | 描述 |
| audio_path | string | 参考音频本地路径 |
| expire_days | int | 有效期（天），-1 表示永久 |
| expires_at | string | 到期时间（ISO 8601），永久则为 null |
| created_at | string | 创建时间（ISO 8601） |

#### 到期自动删除

非永久声音（`expire_days != -1`）在 `expires_at` 后自动删除，包含音频文件与注册记录。

---

### 4. `GET /api/v1/tts/voices` — 列出自定义声音

列出所有已注册的自定义声音。

**请求方式**：`GET`
**Content-Type**：`application/json`

#### 响应示例

```json
{
  "voices": [
    {
      "voice_id": "a1b2c3d4e5f67890",
      "name": "my_voice",
      "engine": "cosyvoice",
      "description": "My custom voice",
      "audio_path": "/workspace/app/models/voices/a1b2c3d4e5f67890/ref.wav",
      "expire_days": 30,
      "expires_at": "2026-11-28T07:19:21Z",
      "created_at": "2026-10-29T07:19:21Z"
    }
  ]
}
```

---

### 5. `DELETE /api/v1/tts/voices/{voice_id}` — 删除自定义声音

按 `voice_id` 删除指定的自定义声音。

**请求方式**：`DELETE`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| voice_id | string | 是 | 要删除的声音 ID |

#### 响应

**成功**：`204 No Content`

**失败**：

| 状态码 | 说明 |
|--------|------|
| `404` | 声音 ID 未找到 |

#### curl 示例

```bash
curl -X DELETE http://localhost:8000/api/v1/tts/voices/a1b2c3d4e5f67890
```

---

## 三、引擎与模型管理接口

### 6. `GET /api/v1/tts/engines` — 列出可用引擎

列出当前所有可用的 TTS 引擎及其支持的音色。

**请求方式**：`GET`
**Content-Type**：`application/json`

#### 响应示例

```json
{
  "engines": [
    {
      "name": "cosyvoice",
      "description": "CosyVoice TTS",
      "voices": ["alice", "bob"],
      "supports_voice_clone": true
    },
    {
      "name": "fishspeech",
      "description": "FishSpeech TTS",
      "voices": ["default"],
      "supports_voice_clone": true
    }
  ]
}
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 引擎名 |
| description | string | 引擎描述 |
| voices | array[string] | 支持的预置音色列表 |
| supports_voice_clone | bool | 是否支持音色克隆 |

---

### 7. `GET /api/v1/tts/models` — 列出已下载模型

列出当前已下载的 TTS 模型。

**请求方式**：`GET`
**Content-Type**：`application/json`

#### 响应示例

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

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 模型标识 |
| engine | string | 所属引擎 |
| path | string | 模型本地路径 |
| size_bytes | int | 模型大小（字节） |
| downloaded_at | string | 下载时间（ISO 8601） |

---

### 8. `POST /api/v1/tts/models/download` — 下载模型

通过 huggingface_hub 下载指定模型到 `models/tts/`。

**请求方式**：`POST`
**Content-Type**：`application/json`

#### 请求示例

```json
{
  "model_id": "cosyvoice",
  "engine": "cosyvoice"
}
```

#### 响应示例

```json
{
  "model_id": "cosyvoice",
  "engine": "cosyvoice",
  "status": "downloaded",
  "path": "/workspace/app/models/tts/cosyvoice"
}
```

---

### 9. `POST /api/v1/tts/models/clear` — 清理模型缓存

清理指定模型的本地缓存。

**请求方式**：`POST`
**Content-Type**：`application/json`

#### 请求示例

```json
{
  "model_id": "cosyvoice"
}
```

#### 响应示例

```json
{
  "model_id": "cosyvoice",
  "status": "cleared"
}
```

---

## 错误响应格式

所有错误均返回 JSON：

```json
{
  "error": {
    "message": "错误描述信息",
    "code": "错误码",
    "status": 400
  }
}
```

常见状态码：

| 状态码 | 说明 |
|--------|------|
| `400` | 请求参数错误（必填字段缺失、参数非法） |
| `404` | 资源未找到（模型、声音、引擎不存在） |
| `500` | 服务内部错误（模型加载、推理失败） |
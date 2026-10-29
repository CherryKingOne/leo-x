# OpenAI 兼容接口文档

完全对齐 OpenAI 官方 TTS 接口格式，可直接对接现有 OpenAI 客户端。

## 基础信息

- **Base URL**：`http://<host>:<port>`
- **鉴权**：暂不支持（后续可加 API Key）
- **Content-Type**：`application/json`

---

## `POST /v1/audio/speech` — 文本转语音

将文本合成为音频，直接返回音频二进制流。

**请求方式**：`POST`
**请求头**：`Content-Type: application/json`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| model | string | 是 | — | 模型名（对应本地已下载模型，如 `tts-1`） |
| input | string | 是 | — | 待合成文本 |
| voice | string | 否 | — | 说话人/音色标识（如 `alloy`、`echo`） |
| response_format | string | 否 | `mp3` | 输出格式：`mp3` / `wav` / `ogg` / `flac` / `pcm` |
| speed | float | 否 | 1.0 | 语速，范围 0.25~4.0 |

### 请求示例

```json
{
  "model": "tts-1",
  "input": "Hello, how are you?",
  "voice": "alloy",
  "response_format": "mp3",
  "speed": 1.0
}
```

### 响应

**成功**：`200 OK`
- **Content-Type**：`application/octet-stream`
- **Body**：音频二进制流，格式由 `response_format` 决定

**失败**：

| 状态码 | 说明 |
|--------|------|
| `400` | 请求参数错误（如必填字段缺失、speed 超出范围） |
| `404` | 模型未找到（`model` 对应的模型未下载） |
| `500` | 服务内部错误（模型加载或推理失败） |

### curl 示例

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, how are you?",
    "voice": "alloy",
    "response_format": "mp3",
    "speed": 1.0
  }' \
  --output output.mp3
```

---

## `GET /v1/models` — 列出可用模型

列出当前所有已下载可用的模型。

**请求方式**：`GET`

### 请求参数

无。

### 响示例

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

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| object | string | 固定为 `list` |
| data | array | 模型列表 |
| data[].id | string | 模型标识（与 `/v1/audio/speech` 的 `model` 参数对应） |
| data[].object | string | 固定为 `model` |
| data[].created | int | 模型创建时间（Unix 时间戳） |
| data[].owned_by | string | 所有者 |

### curl 示例

```bash
curl -X GET http://localhost:8000/v1/models
```

---

## 错误响应格式

所有错误均返回 JSON：

```json
{
  "error": {
    "message": "Model 'tts-1' not found",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
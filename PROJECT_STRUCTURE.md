# 项目目录结构规划（TTS）

按**功能**划分，不引入 DDD 分层。每个模块只承担一件具体职责。

## 目录树

```
workspace/app/
├── README.md
├── pyproject.toml              # uv 项目配置 + 依赖
├── .python-version             # 3.12
├── PROJECT_STRUCTURE.md        # 本文档
├── API_OPENAI.md               # OpenAI 兼容接口文档
├── API_CUSTOM.md               # 自定义接口文档
├── models/                     # 模型本地存放根目录（不进 git）
│   ├── tts/                    # TTS 专用模型目录（用户指定）
│   └── voices/                 # 自定义声音（音色复刻）目录
├── src/app/
│   ├── __init__.py
│   ├── cli.py                  # CLI 入口（typer）
│   ├── config.py               # 配置：模型目录、设备、默认参数
│   ├── api/                    # HTTP 接口层
│   │   ├── __init__.py
│   │   ├── app.py              # FastAPI 应用入口，挂载路由
│   │   ├── openai_compat.py    # OpenAI 兼容接口 (/v1/audio/speech, /v1/models)
│   │   ├── custom_api.py       # 自定义接口 (/api/v1/tts/synthesize, models, engines)
│   │   ├── voices.py           # 自定义声音注册/复刻 (/api/v1/tts/voices)
│   │   └── schemas.py          # Pydantic 请求/响应模型
│   ├── tts/                    # TTS 功能模块
│       ├── __init__.py
│       ├── engine.py           # TTS 引擎抽象（统一调用接口）
│       ├── loader.py           # 通过 transformers 加载模型
│       ├── manager.py          # 通过 huggingface_hub 下载/缓存模型
│       ├── synthesizer.py      # 文本→音频合成流水线
│       └── voice_store.py      # 自定义声音注册/存储（voice_id、有效期管理、到期清理）
└── tests/
    └── tts/                    # TTS 模块测试
```

## 模块职责说明

| 模块 | 职责 | 依赖 |
|------|------|------|
| `cli.py` | 命令行入口，启动服务或单次合成 | typer |
| `config.py` | 读取环境变量/默认值，产出配置对象 | 标准库 |
| `api/app.py` | FastAPI 应用组装，挂载两套路由 | fastapi |
| `api/openai_compat.py` | OpenAI 兼容接口（`/v1/audio/speech`, `/v1/models`） | fastapi |
| `api/custom_api.py` | 自定义接口（`/api/v1/tts/synthesize`、`synthesize-upload`、`models`、`engines`） | fastapi, python-multipart |
| `api/voices.py` | 自定义声音注册/复刻（`/api/v1/tts/voices` 注册、列表、删除） | fastapi, python-multipart |
| `api/schemas.py` | Pydantic 请求/响应模型 | pydantic |
| `tts/engine.py` | 对外暴露的统一 TTS 接口（`TTS` 类） | loader, synthesizer |
| `tts/loader.py` | 调用 `transformers` 实例化模型 | transformers |
| `tts/manager.py` | 调用 `huggingface_hub` 下载/列出/清理模型缓存 | huggingface_hub |
| `tts/synthesizer.py` | 执行文本→音频推理，返回音频字节/路径 | loader |
| `tts/voice_store.py` | 自定义声音注册/存储（voice_id 生成、有效期管理、到期清理） | 标准库 |

## 关键设计点

1. **模型存放**：所有 TTS 模型统一落在 `models/tts/`，由 `config.py` 提供路径，`manager.py` 负责下载到此处。
2. **自定义声音**：音色复刻的参考音频落在 `models/voices/{voice_id}/ref.wav`，由 `tts/voice_store.py` 管理注册（生成 voice_id）、有效期与到期自动清理，`api/voices.py` 提供 HTTP 接口。
3. **加载方式**：统一使用 `transformers` 加载模型。
4. **下载方式**：使用 `huggingface_hub`。
5. **双协议 + 声音复刻**：OpenAI 兼容（`API_OPENAI.md`）+ 自定义接口（`API_CUSTOM.md`），共用 `tts/engine.py` 底层引擎。自定义接口额外支持自定义声音注册/复刻（`api/voices.py`）。
6. **扩展性**：新增 TTS 模型只需在 `loader.py` 增加一个模型注册项，无需改动调用链。

## 依赖

- Python >= 3.12
- huggingface_hub（最新）
- transformers
- typer（CLI）
- fastapi + python-multipart（HTTP 接口）
- pydantic（数据校验）
- httpx（URL 音色克隆）
- numpy（音频处理）
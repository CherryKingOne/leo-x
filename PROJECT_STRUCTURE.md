# 项目目录结构规划（TTS）

按**功能**划分，不引入 DDD 分层。每个模块只承担一件具体职责。

## 目录树

```
workspace/app/
├── README.md
├── pyproject.toml              # uv 项目配置 + 依赖
├── .python-version             # 3.12
├── PROJECT_STRUCTURE.md        # 本文档
├── models/                     # 模型本地存放根目录（不进 git）
│   └── tts/                    # TTS 专用模型目录（用户指定）
├── src/app/
│   ├── __init__.py
│   ├── cli.py                  # CLI 入口（typer）
│   ├── config.py               # 配置：模型目录、设备、默认参数
│   └── tts/                    # TTS 功能模块
│       ├── __init__.py
│       ├── engine.py           # TTS 引擎抽象（统一调用接口）
│       ├── loader.py           # 通过 transformers 加载模型
│       ├── manager.py          # 通过 huggingface_hub 下载/缓存模型
│       └── synthesizer.py      # 文本→音频合成流水线
└── tests/
    └── tts/                    # TTS 模块测试
```

## 模块职责说明

| 模块 | 职责 | 依赖 |
|------|------|------|
| `cli.py` | 命令行入口，解析参数、调用引擎 | typer |
| `config.py` | 读取环境变量/默认值，产出配置对象 | 标准库 |
| `tts/engine.py` | 对外暴露的统一 TTS 接口（`TTS` 类） | loader, synthesizer |
| `tts/loader.py` | 调用 `transformers` 实例化模型 | transformers |
| `tts/manager.py` | 调用 `huggingface_hub` 下载/列出/清理模型缓存 | huggingface_hub |
| `tts/synthesizer.py` | 执行文本→音频推理，返回音频字节/路径 | loader |

## 关键设计点

1. **模型存放**：所有 TTS 模型统一落在 `models/tts/`，由 `config.py` 提供路径，`manager.py` 负责下载到此处。
2. **加载方式**：统一使用 `transformers` 加载模型（用户指定）。
3. **下载方式**：使用 `huggingface_hub`（用户指定）。
4. **扩展性**：新增 TTS 模型只需在 `loader.py` 增加一个模型注册项，无需改动调用链。

## 依赖

- Python >= 3.12
- huggingface_hub（最新）
- transformers
- typer（CLI）
- numpy（音频处理）
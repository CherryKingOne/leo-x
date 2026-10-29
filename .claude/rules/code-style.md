# 项目代码规范

本文档定义本项目的强制代码风格与命名约定。所有 Python 代码必须遵守以下规则，违者视为不合格。

## 一、导入路径：必须使用绝对路径

### 强制（MUST）

项目内所有 Python 代码，**必须使用绝对路径导入**，禁止使用相对路径导入。

### 禁止的写法

```python
# fmt: off
# ❌ 相对导入（禁止）
from ..config import settings
from .tts.engine import TTSEngine
from .schemas import OpenAISpeechRequest
from ..tts.manager import ModelManager
# fmt: on
```

### 正确的写法

```python
# fmt: off
# ✅ 绝对导入（推荐）
from app.config import settings
from app.tts.engine import TTSEngine
from app.api.schemas import OpenAISpeechRequest
from app.tts.manager import ModelManager
# fmt: on
```

### 范围

该规则适用于项目内所有 `import` 和 `from ... import ...` 语句，包括：
- 模块内部导入
- 跨模块导入
- 测试文件导入

## 二、命名：禁止下划线开头

### 强制（MUST NOT）

项目内所有 Python 代码中，**禁止出现以下划线 `_` 开头的函数、方法或类定义**。

### 具体禁止的命名

以下写法在项目中属于**违规**：

```python
# fmt: off
# ❌ 模块级函数
def _helper():
    ...

# ❌ 异步函数
async def _helper():
    ...

# ❌ 类
class _Helper:
    ...

# ❌ 类方法
class Service:
    def _method(self):
        ...

# ❌ 静态方法
class Service:
    @staticmethod
    def _method():
        ...

# ❌ 类方法（classmethod）
class Service:
    @classmethod
    def _method(cls):
        ...
# fmt: on
```

### 禁止调用以下划线开头的方法

因为项目中不应存在此类定义，所以**禁止调用以下划线开头的方法**：

```python
# fmt: off
_text.str()          # ❌ _text 不应存在
some_obj._internal() # ❌ _internal 不应存在
# fmt: on
```

### 允许的命名

以下写法是**允许**的：

```python
# fmt: off
# ✅ 普通函数
def helper():
    ...

# ✅ 异步函数
async def helper():
    ...

# ✅ 类
class Helper:
    ...

# ✅ 类方法
class Service:
    def method(self):
        ...

# ✅ 双下划线魔术方法（Python 协议保留名，予以豁免）
def __init__(self):
    ...
def __str__(self):
    ...
# fmt: on
```

### 变量命名建议

虽然规则主要约束函数/方法/类名，但建议模块级、类成员变量也避免以下划线开头，保持命名风格一致。

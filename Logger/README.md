# PyEasyLogger

> **注意：这是一个个人自用/内部使用的 Python 日志封装模块。**
>
> 它基于 Python 标准库 `logging` 进行了简单的封装，旨在提供更美观的控制台输出（支持颜色）和更清晰的异常堆栈显示。代码风格偏向个人习惯，可能不包含大型生产级库的所有边缘情况处理，但足以满足日常脚本和中小型项目的调试需求。

## 特性

*   **彩色控制台输出**：自动检测终端支持，为不同日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）添加颜色高亮。
*   **友好的异常格式化**：当记录异常时，使用分隔线包裹堆栈跟踪信息，使其在日志文件中更易阅读。
*   **开箱即用**：默认提供全局 `auto_logger实例，无需复杂配置即可开始记录日志。
*   **灵活扩展**：支持动态修改日志文件路径、移除默认 Handler 并添加自定义 Handler。
*   **自动装饰器**：提供 `@add_auto_log` 装饰器，自动记录函数的调用、完成及异常状态。

## 安装

由于这是自用模块，建议直接将其作为文件引入你的项目，或通过 Git Submodule 方式管理。

1.  下载 `logger.py` (假设你将上述代码保存为此文件名)。
2.  将其放入你的项目目录中。

```python
from logger import Logger, auto_logger, add_auto_log
```

## 快速开始

### 1. 基础使用

最简单的用法是直接导入并使用默认的 `auto_logger`。默认日志级别为 `WARNING`。

```python
from logger import auto_logger
auto_logger.setLevel("INFO")

auto_logger.info("这是一条信息消息")
auto_logger.warning("这是一条警告消息")
auto_logger.error("这是一条错误消息")

try:
    1 / 0
except Exception:
    auto_logger.exception("捕获到一个异常")
```

### 2. 创建独立 Logger 实例

如果你需要为不同模块创建独立的 Logger，可以实例化 `Logger` 类。

```python
from logger import Logger

my_logger = Logger(logger_name="my_module", save_path="./logs/app.log")

my_logger.setLevel("DEBUG")
my_logger.debug("debug message")
```

### 3. 使用自动日志装饰器

使用 `@add_auto_log` 装饰器可以自动记录函数的进入、退出以及任何未捕获的异常。

```python
from logger import add_auto_log, auto_logger

# 确保设置了合适的日志级别，否则 INFO 级别的调用日志不会显示
auto_logger.setLevel("INFO")

@add_auto_log
def my_function(x, y):
    return x + y

result = my_function(1, 2)

# 控制台输出示例:
# 2026-04-08 10:00:00 | INFO     | logger:XX -> 'my_function' is called.
# 2026-04-08 10:00:00 | INFO     | logger:XX -> 'my_function' is done.
```

## 高级配置

### 修改日志文件路径

你可以动态地更改或设置日志文件的保存路径。如果传入空字符串 `""`，则会移除文件日志处理器，仅保留控制台输出。

```python
from logger import auto_logger
auto_logger.set_log_path("./logs/new_log.log")

# 传入空字符串 `""`，移除文件日志处理器，仅保留控制台输出。
auto_logger.set_log_path("")
```

### 完全自定义 Handler

如果你想完全控制日志行为（例如发送日志到远程服务器），你可以移除默认的 Handler 并添加你自己的。

```python
import logging
from logger import Logger

my_logger = Logger()

# 1. 移除默认的控制台和文件 Handler
if hasattr(my_logger, 'stream_handler'):
    my_logger.removeHandler(my_logger.stream_handler)
if hasattr(my_logger, 'file_handler'):
    my_logger.removeHandler(my_logger.file_handler)

# 2. 添加你自己的 Handler
custom_handler = logging.StreamHandler()
custom_format = logging.Formatter('CUSTOM: %(message)s')
custom_handler.setFormatter(custom_format)
my_logger.addHandler(custom_handler)

my_logger.warning("自定义格式输出")
```

## 文件结构说明

*   `_SysExcInfoFormatter`: 内部类，用于格式化异常堆栈，添加 `===` 边框以便区分。
*   `_ColorFormatter`: 内部类，用于控制台彩色输出。在非 TTY 环境（如重定向到文件）下会自动退化为普通格式。
*   `Logger`: 主类，封装了 `logging.Logger` 的常用方法。
*   `auto_logger`: 模块加载时自动创建的全局 Logger 实例。
*   `add_auto_log`: 装饰器，用于自动包装函数调用日志。

## 注意事项

1.  **线程安全**：底层依赖 Python 标准的 `logging` 模块，但本模块线程不安全！！！
2.  **编码**：默认文件编码为 `utf-8`。
3.  **自用声明**：此模块主要用于个人开发效率提升。如果在生产环境中使用，请根据具体需求进行充分测试。

## 📄 许可证

MIT License

---

*Created by [TemautXBXBSAA]

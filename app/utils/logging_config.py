import structlog
import logging
import sys
import os
from typing import Any, Dict
from prometheus_client import Counter, Histogram, Gauge


# Prometheus监控指标
# HTTP请求总数，按方法、端点和状态码分类
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
# HTTP请求持续时间，按方法和端点分类
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
# 活跃连接数
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')

# 任务处理总数，按状态（成功/错误）分类
TASK_PROCESSED = Counter('tasks_processed_total', 'Total tasks processed', ['status'])
# 任务处理持续时间
TASK_DURATION = Histogram('task_processing_duration_seconds', 'Task processing duration')

# 错误总数，按错误类型和端点分类
ERROR_COUNT = Counter('errors_total', 'Total errors', ['type', 'endpoint'])


def configure_structlog() -> None:
    """配置structlog用于结构化日志记录"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """获取已配置的structlog日志记录器"""
    return structlog.get_logger(name)


# 初始化structlog配置
configure_structlog()

# 获取根日志记录器进行配置
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 创建控制台处理器
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# 创建格式化器并添加到处理器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 将处理器添加到根日志记录器
root_logger.addHandler(handler)

# 如果在生产环境中，也添加文件处理器
if os.getenv("ENVIRONMENT") == "production":
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
import time
import sentry_sdk
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import products
from app.database import init_db
from app.socket import sio_app
from app.utils.logging_config import get_logger, REQUEST_COUNT, REQUEST_DURATION, ACTIVE_CONNECTIONS, ERROR_COUNT

# 初始化日志记录器
logger = get_logger(__name__)

# 初始化Sentry
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()
    # 记录应用启动日志
    logger.info("Application startup", extra={"event": "startup"})

@app.on_event("shutdown")
def on_shutdown():
    # 记录应用关闭日志
    logger.info("Application shutdown", extra={"event": "shutdown"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加中间件用于请求/响应日志记录和指标收集
@app.middleware("http")
async def log_requests_and_metrics(request: Request, call_next):
    start_time = time.time()
    # 增加活跃连接数
    ACTIVE_CONNECTIONS.inc()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 记录请求日志
        logger.info(
            "Request processed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        # 更新Prometheus监控指标
        REQUEST_COUNT.labels(method=request.method, endpoint=str(request.url), status=response.status_code).inc()
        REQUEST_DURATION.labels(method=request.method, endpoint=str(request.url)).observe(process_time)
        
        return response
    except Exception as e:
        # 记录错误日志
        logger.error(
            "Request processing error",
            extra={
                "method": request.method,
                "url": str(request.url),
                "error": str(e)
            }
        )
        
        # 更新错误计数器
        ERROR_COUNT.labels(type="request_processing", endpoint=str(request.url)).inc()
        
        # 重新抛出异常以便Sentry捕获
        raise
    finally:
        # 减少活跃连接数
        ACTIVE_CONNECTIONS.dec()

# 暴露Prometheus指标端点
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
def metrics():
    # 返回Prometheus指标
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

app.include_router(products.router, prefix="/api")
app.mount('/', sio_app)

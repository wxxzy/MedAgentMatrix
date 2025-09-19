import uuid
import json
import time
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.product_service import process_product_task, save_approved_product_task
from app.models.schema import ReviewQueue, MasterProduct, ProcessRequest
from app.database import SessionLocal
from app.agents.graph import AgentState
from app.utils.logging_config import get_logger, REQUEST_COUNT, REQUEST_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

router = APIRouter()

tasks = {}

@router.post("/products/process")
async def process_product(request: ProcessRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "PROCESSING", "history": []}
    background_tasks.add_task(process_product_task, request.raw_text, task_id, tasks, request.sid)
    
    # 更新监控指标
    REQUEST_COUNT.labels(method="POST", endpoint="/api/products/process", status=200).inc()
    REQUEST_DURATION.labels(method="POST", endpoint="/api/products/process").observe(time.time() - start_time)
    
    return {"task_id": task_id, "status": "PROCESSING"}

@router.get("/products/status/{task_id}")
def get_status(task_id: str):
    start_time = time.time()
    task_info = tasks.get(task_id)
    if not task_info:
        # 更新错误监控指标
        REQUEST_COUNT.labels(method="GET", endpoint="/api/products/status/{task_id}", status=404).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/api/products/status/{task_id}").observe(time.time() - start_time)
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 更新监控指标
    REQUEST_COUNT.labels(method="GET", endpoint="/api/products/status/{task_id}", status=200).inc()
    REQUEST_DURATION.labels(method="GET", endpoint="/api/products/status/{task_id}").observe(time.time() - start_time)
    
    return task_info

@router.get("/products/review/queue")
def get_review_queue():
    start_time = time.time()
    db = SessionLocal()
    try:
        items = db.query(ReviewQueue).filter(ReviewQueue.status == 'PENDING').all()
        
        # 更新监控指标
        REQUEST_COUNT.labels(method="GET", endpoint="/api/products/review/queue", status=200).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/api/products/review/queue").observe(time.time() - start_time)
        
        return items
    except Exception as e:
        # 更新错误监控指标
        REQUEST_COUNT.labels(method="GET", endpoint="/api/products/review/queue", status=500).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/api/products/review/queue").observe(time.time() - start_time)
        raise
    finally:
        db.close()

@router.post("/products/review/submit/{review_id}")
async def submit_review(review_id: int, approved: bool, background_tasks: BackgroundTasks, sid: str = None):
    start_time = time.time()
    db = SessionLocal()
    try:
        item = db.query(ReviewQueue).filter(ReviewQueue.review_id == review_id).first()
        if not item:
            # 更新错误监控指标
            REQUEST_COUNT.labels(method="POST", endpoint="/api/products/review/submit/{review_id}", status=404).inc()
            REQUEST_DURATION.labels(method="POST", endpoint="/api/products/review/submit/{review_id}").observe(time.time() - start_time)
            raise HTTPException(status_code=404, detail="Review item not found")
        if item.status != 'PENDING':
            # 更新错误监控指标
            REQUEST_COUNT.labels(method="POST", endpoint="/api/products/review/submit/{review_id}", status=400).inc()
            REQUEST_DURATION.labels(method="POST", endpoint="/api/products/review/submit/{review_id}").observe(time.time() - start_time)
            raise HTTPException(status_code=400, detail=f"Review item has already been processed with status: {item.status}")

        decision = "APPROVED" if approved else "REJECTED"
        item.status = decision
        db.commit()

        if approved:
            # 准备save_product agent的状态
            state_to_save = {
                "product_type": item.product_type,
                "validated_data": json.loads(item.validated_data),
                "current_node": "save_product" # 显式设置当前节点
            }
            
            task_id = str(uuid.uuid4())
            tasks[task_id] = {"status": f"SAVING_APPROVED_PRODUCT", "history": [] }
            
            # 调用新的专用服务任务
            background_tasks.add_task(save_approved_product_task, state_to_save, task_id, tasks, sid)
            
            # 更新监控指标
            REQUEST_COUNT.labels(method="POST", endpoint="/api/products/review/submit/{review_id}", status=200).inc()
            REQUEST_DURATION.labels(method="POST", endpoint="/api/products/review/submit/{review_id}").observe(time.time() - start_time)
            
            return {"status": "SUCCESS", "review_id": review_id, "new_status": decision, "continuation_task_id": task_id}
        else:
            # 如果被拒绝，只更新状态，不执行其他操作
            
            # 更新监控指标
            REQUEST_COUNT.labels(method="POST", endpoint="/api/products/review/submit/{review_id}", status=200).inc()
            REQUEST_DURATION.labels(method="POST", endpoint="/api/products/review/submit/{review_id}").observe(time.time() - start_time)
            
            return {"status": "SUCCESS", "review_id": review_id, "new_status": decision}

    finally:
        db.close()

@router.get("/products")
def get_all_products():
    start_time = time.time()
    db = SessionLocal()
    try:
        products = db.query(MasterProduct).all()
        
        # 更新监控指标
        REQUEST_COUNT.labels(method="GET", endpoint="/api/products", status=200).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/api/products").observe(time.time() - start_time)
        
        return products
    except Exception as e:
        # 更新错误监控指标
        REQUEST_COUNT.labels(method="GET", endpoint="/api/products", status=500).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/api/products").observe(time.time() - start_time)
        raise
    finally:
        db.close()
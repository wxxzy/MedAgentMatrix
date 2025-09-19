import random
import time
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

def query_nmpa(approval_number: str) -> dict:
    """模拟查询NMPA数据库"""
    start_time = time.time()
    # 记录查询NMPA的日志
    logger.info(f"Querying NMPA for: {approval_number}")
    # 在实际场景中，这将涉及API调用或网页抓取。
    # 在这个MVP中，我们将模拟结果。
    if not approval_number or "H" not in approval_number:
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc() # 逻辑正常工作，但结果无效
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"status": "INVALID_FORMAT", "data": None}
    
    # 模拟小概率找不到有效编号的情况
    if random.random() < 0.1:
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc() # 逻辑正常工作，但未找到结果
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"status": "NOT_FOUND", "data": None}
    
    # 更新监控指标
    TASK_PROCESSED.labels(status="success").inc()
    TASK_DURATION.observe(time.time() - start_time)
    
    return {
        "status": "FOUND",
        "data": {
            "approval_number": approval_number,
            "product_name": "模拟药品名称",
            "manufacturer": "模拟生产厂家"
        }
    }

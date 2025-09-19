import time
from app.database import SessionLocal
from app.models.schema import ReviewQueue
import json
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

def request_review(state):
    """将数据保存到数据库的审核队列中并暂停工作流"""
    start_time = time.time()
    # 记录Human in the Loop Agent开始执行
    logger.info("---HUMAN IN THE LOOP AGENT---")
    reason = state.get("review_reason", "未知原因，需要人工审核。")
    
    db = SessionLocal()
    try:
        review_item = ReviewQueue(
            raw_info=json.dumps({"raw_text": state.get("raw_text")}),
            extracted_data=json.dumps(state.get("extracted_data", {})),
            validated_data=json.dumps(state.get("validated_data", {})),
            product_type=state.get("product_type"),
            review_reason=reason,
            status="PENDING"
        )
        db.add(review_item)
        db.commit()
        db.refresh(review_item)
        review_id = review_item.review_id
        # 记录保存到审核队列的日志
        logger.info(f"Saved item to review queue with ID: {review_id}")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"review_id": review_id, "review_reason": reason, "current_node": "request_review"}
    except Exception as e:
        # 记录Human in the Loop Agent执行失败日志
        logger.error(f"Human in the loop Agent执行失败: {e}")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="error").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        # 重新抛出异常
        raise
    finally:
        db.close()

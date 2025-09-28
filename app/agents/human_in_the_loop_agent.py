import time
from app.database import SessionLocal
from app.models.schema import ReviewQueue
import json
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION
from typing import Dict, Any, List

# 初始化日志记录器
logger = get_logger(__name__)

def calculate_priority_score(state: Dict[str, Any]) -> int:
    """计算审核项的优先级评分"""
    score = 0
    review_reason = state.get("review_reason", "")
    
    # 根据审核原因类型评分
    if "关键字段" in review_reason or "批准文号" in review_reason:
        score += 50
    elif "数据冲突" in review_reason:
        score += 30
    else:
        score += 10
        
    # 根据匹配相似度评分（如果有）
    match_result = state.get("match_result", {})
    if match_result.get("status") == "HIGH_SIMILARITY":
        score += 20
        
    return min(score, 100) # 限制最高分为100

def request_review(state):
    """将数据保存到数据库的审核队列中并暂停工作流"""
    start_time = time.time()
    # 记录Human in the Loop Agent开始执行
    logger.info("---HUMAN IN THE LOOP AGENT---")
    
    # 构造结构化的审核原因
    review_reasons = []
    raw_reason = state.get("review_reason", "未知原因，需要人工审核。")
    if isinstance(raw_reason, str):
        review_reasons = [{
            "type": "UNKNOWN",
            "message": raw_reason
        }]
    elif isinstance(raw_reason, list):
        review_reasons = raw_reason
    else:
        review_reasons = [{
            "type": "UNKNOWN",
            "message": str(raw_reason)
        }]
    
    # 获取Agent处理历史
    agent_history = state.get("agent_history", [])
    
    # 获取匹配候选产品
    match_candidates = []
    match_result = state.get("match_result", {})
    if match_result.get("candidates"):
        match_candidates = match_result["candidates"]
        
    # 获取融合冲突详情
    fusion_conflicts = []
    fusion_result = state.get("fusion_result", {})
    if fusion_result.get("conflicts"):
        fusion_conflicts = fusion_result["conflicts"]
    
    # 计算优先级评分
    priority_score = calculate_priority_score(state)
    
    db = SessionLocal()
    try:
        review_item = ReviewQueue(
            raw_info=state.get("raw_text", ""),
            extracted_data=state.get("extracted_data", {}),
            validated_data=state.get("validated_data", {}),
            product_type=state.get("product_type"),
            review_reason=review_reasons,
            agent_history=agent_history,
            match_candidates=match_candidates,
            fusion_conflicts=fusion_conflicts,
            priority_score=priority_score,
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
        
        return {
            "review_id": review_id, 
            "review_reason": review_reasons,
            "priority_score": priority_score,
            "current_node": "request_review"
        }
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

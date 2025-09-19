import time
from app.database import SessionLocal
from app.models.schema import MasterProduct
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

def match_product(state):
    start_time = time.time()
    # 记录Matcher Agent开始执行
    logger.info("---MATCHER AGENT---")
    db = SessionLocal()
    try:
        validated_data = state.get("validated_data", {})
        approval_number = validated_data.get("approval_number")
        
        match_result = {"status": "NO_MATCH", "spu_id": None}

        if approval_number:
            # 记录尝试通过批准文号匹配的日志
            logger.info(f"Attempting to match by approval number: {approval_number}")
            product = db.query(MasterProduct).filter(MasterProduct.approval_number == approval_number).first()
            if product:
                # 记录找到匹配项的日志
                logger.info(f"Match found for approval number {approval_number}. SPU ID: {product.spu_id}")
                match_result = {"status": "MATCH", "spu_id": product.spu_id}
            else:
                # 记录未找到匹配项的日志
                logger.info(f"No match found for approval number: {approval_number}")
        else:
            # 记录未提供批准文号，跳过匹配的日志
            logger.info("No approval number provided, skipping match.")

        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"match_result": match_result, "current_node": "matcher"}
    except Exception as e:
        # 记录Matcher Agent执行失败日志
        logger.error(f"Matcher Agent执行失败: {e}")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="error").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        # 重新抛出异常
        raise
    finally:
        db.close()

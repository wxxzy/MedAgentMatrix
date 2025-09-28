import time
from app.database import SessionLocal
from app.models.schema import MasterProduct
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

def merge_product_data(existing_product, new_data):
    """合并产品数据"""
    fused_data = {}
    conflicts = []
    
    # 定义字段处理规则
    # 关键字段（必须一致）
    critical_fields = ["product_type", "approval_number"]
    
    # 重要字段（需要比较和可能合并）
    important_fields = ["product_name", "manufacturer", "specification"]
    
    # 一般字段（可以合并）
    general_fields = [
        "brand", "barcode", "mah", "dosage_form", 
        "product_technical_requirements_number", "registration_classification",
        "main_ingredients", "execution_standard"
    ]
    
    # 检查关键字段是否一致
    for field in critical_fields:
        existing_value = getattr(existing_product, field, None)
        new_value = new_data.get(field)
        if existing_value and new_value and str(existing_value) != str(new_value):
            conflicts.append({
                "field": field,
                "existing_value": existing_value,
                "new_value": new_value,
                "reason": "关键字段不匹配"
            })
        else:
            # 如果现有产品有值，使用现有值；否则使用新值
            fused_data[field] = existing_value if existing_value else new_value
    
    # 如果存在关键字段冲突，直接返回冲突，不进行后续处理
    if conflicts:
        return None, conflicts
    
    # 处理重要字段
    for field in important_fields:
        existing_value = getattr(existing_product, field, None) or ""
        new_value = new_data.get(field, "") or ""
        
        # 如果新值不为空且与现有值不同，需要判断
        if new_value and str(existing_value) != str(new_value):
            # 简单的合并策略：优先保留非空值
            # 更复杂的策略可以在这里实现
            if not existing_value:
                fused_data[field] = new_value
            else:
                # 两者都有值但不同，标记为冲突
                conflicts.append({
                    "field": field,
                    "existing_value": existing_value,
                    "new_value": new_value,
                    "reason": "重要字段值不同"
                })
                # 在融合数据中保留现有值
                fused_data[field] = existing_value
        else:
            # 使用现有值或新值（如果现有值为空）
            fused_data[field] = existing_value if existing_value else new_value
    
    # 处理一般字段
    for field in general_fields:
        existing_value = getattr(existing_product, field, None) or ""
        new_value = new_data.get(field, "") or ""
        
        # 简单的合并策略：优先保留非空值
        if not existing_value and new_value:
            fused_data[field] = new_value
        else:
            fused_data[field] = existing_value
    
    return fused_data, conflicts

def fuse_product(state):
    """融合产品数据"""
    start_time = time.time()
    # 记录Fusion Agent开始执行
    logger.info("---FUSION AGENT---")
    
    try:
        validated_data = state.get("validated_data", {})
        match_result = state.get("match_result", {})
        product_type = state.get("product_type", "")
        
        fusion_result = {
            "status": "NEW_PRODUCT",
            "fused_data": validated_data,
            "conflicts": [],
            "spu_id": None
        }
        
        # 根据匹配结果进行不同处理
        match_status = match_result.get("status")
        
        if match_status == "MATCH":
            # 完全匹配，直接使用现有产品数据
            spu_id = match_result.get("spu_id")
            db = SessionLocal()
            try:
                existing_product = db.query(MasterProduct).filter(MasterProduct.spu_id == spu_id).first()
                if existing_product:
                    # 对于完全匹配，我们可能只需要更新时间戳
                    # 或者根据业务需求决定是否需要合并其他字段
                    fusion_result = {
                        "status": "FUSED",
                        "fused_data": {
                            "product_type": existing_product.product_type,
                            "product_name": existing_product.product_name,
                            "brand": existing_product.brand,
                            "manufacturer": existing_product.manufacturer,
                            "approval_number": existing_product.approval_number,
                            "specification": existing_product.specification,
                            "barcode": existing_product.barcode,
                            "mah": existing_product.mah,
                            "dosage_form": existing_product.dosage_form,
                            "product_technical_requirements_number": existing_product.product_technical_requirements_number,
                            "registration_classification": existing_product.registration_classification,
                            "main_ingredients": existing_product.main_ingredients,
                            "execution_standard": existing_product.execution_standard
                        },
                        "conflicts": [],
                        "spu_id": spu_id
                    }
                    logger.info(f"完全匹配，使用现有产品数据，SPU ID: {spu_id}")
                else:
                    logger.warning(f"匹配到的SPU ID {spu_id} 在数据库中未找到")
            finally:
                db.close()
                
        elif match_status in ["HIGH_SIMILARITY", "CANDIDATES"]:
            # 高度相似或有候选产品，需要数据融合
            spu_id = match_result.get("spu_id")
            if spu_id:
                db = SessionLocal()
                try:
                    existing_product = db.query(MasterProduct).filter(MasterProduct.spu_id == spu_id).first()
                    if existing_product:
                        # 合并数据
                        fused_data, conflicts = merge_product_data(existing_product, validated_data)
                        
                        if conflicts:
                            # 存在冲突，需要人工审核
                            fusion_result = {
                                "status": "NEEDS_REVIEW",
                                "fused_data": fused_data,
                                "conflicts": conflicts,
                                "spu_id": spu_id
                            }
                            logger.info(f"数据融合发现冲突，需要人工审核，SPU ID: {spu_id}")
                        else:
                            # 无冲突，可以自动融合
                            fusion_result = {
                                "status": "FUSED",
                                "fused_data": fused_data,
                                "conflicts": [],
                                "spu_id": spu_id
                            }
                            logger.info(f"数据融合成功，SPU ID: {spu_id}")
                    else:
                        logger.warning(f"匹配到的SPU ID {spu_id} 在数据库中未找到")
                finally:
                    db.close()
            else:
                # 没有明确的匹配产品，作为新产品处理
                fusion_result = {
                    "status": "NEW_PRODUCT",
                    "fused_data": validated_data,
                    "conflicts": [],
                    "spu_id": None
                }
                logger.info("没有明确匹配产品，作为新产品处理")
                
        else:
            # 没有匹配或未定义的匹配状态，作为新产品处理
            fusion_result = {
                "status": "NEW_PRODUCT",
                "fused_data": validated_data,
                "conflicts": [],
                "spu_id": None
            }
            logger.info("没有匹配结果，作为新产品处理")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"fusion_result": fusion_result, "current_node": "fusion"}
    except Exception as e:
        # 记录Fusion Agent执行失败日志
        logger.error(f"Fusion Agent执行失败: {e}")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="error").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        # 重新抛出异常
        raise
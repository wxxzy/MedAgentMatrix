import time
from app.database import SessionLocal
from app.models.schema import MasterProduct
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

def save_product(state):
    """将验证后的产品数据保存到master_products表中"""
    start_time = time.time()
    # 记录Save Product Agent开始执行
    logger.info("---SAVE PRODUCT AGENT---")
    validated_data = state.get("validated_data")
    product_type = state.get("product_type")

    if not validated_data or not product_type:
        # 记录保存产品失败日志
        logger.error("Error: Cannot save product, validated_data or product_type is missing.")
        return {"error": "Cannot save product, validated_data or product_type is missing.", "current_node": "save_product"}

    db = SessionLocal()
    try:
        new_product = MasterProduct(
            product_type=product_type,
            product_name=validated_data.get("product_name"),
            brand=validated_data.get("brand"),
            manufacturer=validated_data.get("manufacturer"),
            approval_number=validated_data.get("approval_number"),
            specification=validated_data.get("specification"),
            barcode=validated_data.get("barcode"),
            mah=validated_data.get("mah"),
            dosage_form=validated_data.get("dosage_form"),
            product_technical_requirements_number=validated_data.get("product_technical_requirements_number"),
            registration_classification=validated_data.get("registration_classification"),
            main_ingredients=validated_data.get("main_ingredients"),
            execution_standard=validated_data.get("execution_standard")
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        spu_id = new_product.spu_id
        # 记录成功保存新产品日志
        logger.info(f"Successfully saved new product with SPU ID: {spu_id}")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"spu_id": spu_id, "current_node": "save_product"}
    except Exception as e:
        # 记录保存产品到数据库失败日志
        logger.error(f"Error saving product to database: {e}")
        db.rollback()
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="error").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"error": str(e), "current_node": "save_product"}
    finally:
        db.close()

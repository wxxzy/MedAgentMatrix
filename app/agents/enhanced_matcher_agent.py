import time
import re
from difflib import SequenceMatcher
from app.database import SessionLocal
from app.models.schema import MasterProduct
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

def calculate_similarity(str1, str2):
    """计算两个字符串的相似度"""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def calculate_match_score(validated_data, product):
    """计算匹配分数"""
    score = 0
    
    # 批准文号匹配（权重40%）
    approval_number_new = validated_data.get("approval_number", "")
    approval_number_existing = product.approval_number or ""
    if approval_number_new and approval_number_existing:
        if approval_number_new == approval_number_existing:
            score += 40
        elif approval_number_new.startswith(approval_number_existing) or approval_number_existing.startswith(approval_number_new):
            score += 20
    
    # 产品名称匹配（权重25%）
    product_name_new = validated_data.get("product_name", "")
    product_name_existing = product.product_name or ""
    name_similarity = calculate_similarity(product_name_new, product_name_existing)
    if name_similarity > 0.9:
        score += 25
    elif name_similarity > 0.8:
        score += 20
    elif name_similarity > 0.7:
        score += 15
    elif name_similarity > 0.6:
        score += 10
    
    # 生产企业匹配（权重20%）
    manufacturer_new = validated_data.get("manufacturer", "")
    manufacturer_existing = product.manufacturer or ""
    if manufacturer_new and manufacturer_existing:
        manufacturer_similarity = calculate_similarity(manufacturer_new, manufacturer_existing)
        if manufacturer_similarity > 0.9:
            score += 20
        elif manufacturer_similarity > 0.8:
            score += 10
    
    # 规格匹配（权重10%）
    specification_new = validated_data.get("specification", "")
    specification_existing = product.specification or ""
    if specification_new and specification_existing:
        spec_similarity = calculate_similarity(specification_new, specification_existing)
        if spec_similarity > 0.9:
            score += 10
        elif spec_similarity > 0.8:
            score += 5
    
    # 品牌匹配（权重5%）
    brand_new = validated_data.get("brand", "")
    brand_existing = product.brand or ""
    if brand_new and brand_existing:
        brand_similarity = calculate_similarity(brand_new, brand_existing)
        if brand_similarity > 0.9:
            score += 5
        elif brand_similarity > 0.8:
            score += 2
    
    return score

def find_matching_products(validated_data, threshold=40, limit=10):
    """查找匹配的产品"""
    db = SessionLocal()
    try:
        # 构建查询条件
        query = db.query(MasterProduct)
        
        # 如果有批准文号，优先按批准文号精确匹配
        approval_number = validated_data.get("approval_number")
        if approval_number:
            query = query.filter(MasterProduct.approval_number == approval_number)
            products = query.all()
            if products:
                # 如果找到精确匹配的批准文号，只返回这些产品
                candidates = []
                for product in products:
                    score = calculate_match_score(validated_data, product)
                    candidates.append({
                        "product": product,
                        "score": score
                    })
                return candidates[:limit]
        
        # 如果没有批准文号或没有精确匹配，进行模糊匹配
        # 这里可以添加更多过滤条件以提高性能
        products = query.limit(100).all()  # 限制查询数量以提高性能
        
        # 计算匹配分数
        candidates = []
        for product in products:
            score = calculate_match_score(validated_data, product)
            if score >= threshold:
                candidates.append({
                    "product": product,
                    "score": score
                })
        
        # 按分数排序并返回前N个
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:limit]
    finally:
        db.close()

def match_product(state):
    start_time = time.time()
    # 记录Matcher Agent开始执行
    logger.info("---MATCHER AGENT---")
    
    try:
        validated_data = state.get("validated_data", {})
        
        # 查找匹配的产品
        candidates = find_matching_products(validated_data)
        
        match_result = {
            "status": "NO_MATCH",
            "spu_id": None,
            "candidates": []
        }
        
        if candidates:
            best_match = candidates[0]
            best_score = best_match["score"]
            
            # 根据分数确定匹配状态
            if best_score >= 90:
                # 完全匹配
                match_result = {
                    "status": "MATCH",
                    "spu_id": best_match["product"].spu_id,
                    "candidates": []
                }
                logger.info(f"完全匹配找到，SPU ID: {best_match['product'].spu_id}, 分数: {best_score}")
            elif best_score >= 75:
                # 高度相似
                match_result = {
                    "status": "HIGH_SIMILARITY",
                    "spu_id": best_match["product"].spu_id,
                    "candidates": [
                        {
                            "spu_id": candidate["product"].spu_id,
                            "score": candidate["score"],
                            "product_info": {
                                "product_name": candidate["product"].product_name,
                                "manufacturer": candidate["product"].manufacturer,
                                "approval_number": candidate["product"].approval_number
                            }
                        } for candidate in candidates[:5]  # 返回前5个候选
                    ]
                }
                logger.info(f"高度相似产品找到，最佳匹配SPU ID: {best_match['product'].spu_id}, 分数: {best_score}")
            else:
                # 返回候选结果
                match_result = {
                    "status": "CANDIDATES",
                    "spu_id": None,
                    "candidates": [
                        {
                            "spu_id": candidate["product"].spu_id,
                            "score": candidate["score"],
                            "product_info": {
                                "product_name": candidate["product"].product_name,
                                "manufacturer": candidate["product"].manufacturer,
                                "approval_number": candidate["product"].approval_number
                            }
                        } for candidate in candidates[:10]  # 返回前10个候选
                    ]
                }
                logger.info(f"找到{len(candidates)}个候选产品，最高分数: {best_score}")
        else:
            # 没有找到匹配的产品
            logger.info("没有找到匹配的产品")
        
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
import time
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from app.utils.llm_utils import get_llm_instance # 导入统一的LLM获取函数
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

load_dotenv()

# 初始化日志记录器
logger = get_logger(__name__)

def get_classifier_chain():
    llm = get_llm_instance() # 使用统一函数获取LLM实例
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个商品分类专家。根据提供的商品信息，判断其最可能的商品类型。类型选项为：[药品, 器械, 药妆, 保健品, 中药饮片, 普通商品]。请重点关注'批准文号'、'注册证号'等关键词。仅返回类型名称，不要包含任何其他文字或解释。如果无法判断，返回'普通商品'。"),
        ("user", "{raw_text}")
    ])
    return prompt | llm

def classify_product(state):
    start_time = time.time()
    # 记录Classifier Agent开始执行
    logger.info("---CLASSIFIER AGENT---")
    raw_text = state["raw_text"]
    
    try:
        classifier_chain = get_classifier_chain()
        product_type = classifier_chain.invoke({"raw_text": raw_text}).content.strip()
        
        product_type = product_type.replace("。", "").replace("：", "").replace(" ", "")
        if product_type not in ["药品", "器械", "药妆", "保健品", "中药饮片", "普通商品"]:
            product_type = "普通商品"

        # 记录分类结果
        logger.info(f"Classifier output: '{product_type}'")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"product_type": product_type, "current_node": "classifier"}
    except Exception as e:
        # 记录错误日志
        logger.error(
            "Classifier agent error",
            extra={
                "error": str(e),
                "raw_text": raw_text
            }
        )
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="error").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        # 重新抛出异常
        raise

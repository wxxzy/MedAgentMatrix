import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from app.utils.llm_utils import get_llm_instance # 导入统一的LLM获取函数
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

load_dotenv()

# 初始化日志记录器
logger = get_logger(__name__)

class DrugInfo(BaseModel):
    approval_number: str = Field(description="批准文号")
    product_name: str = Field(description="通用名 / 商品名")
    brand: Optional[str] = Field(description="品牌")
    specification: str = Field(description="规格")
    manufacturer: str = Field(description="生产企业")
    dosage_form: Optional[str] = Field(description="剂型")
    mah: Optional[str] = Field(description="上市许可持有人")

def extract_drug_info(state):
    start_time = time.time()
    # 记录Drug Extractor Agent开始执行
    logger.info("---DRUG EXTRACTOR AGENT---")
    raw_text = state["raw_text"]
    
    try:
        llm = get_llm_instance() # 使用统一函数获取LLM实例

        parser = JsonOutputParser(pydantic_object=DrugInfo)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个药品信息提取专家。请从提供的商品信息中，严格按照以下JSON Schema提取药品的相关属性。
            如果某个字段在原文中未提及，请返回空字符串"""),
            ("human", "{raw_text}\n{format_instructions}")
        ]).partial(format_instructions=parser.get_format_instructions())

        chain = prompt | llm | parser
        
        extracted_data = chain.invoke({"raw_text": raw_text})
        
        # 记录提取的药品信息
        logger.info(f"Extracted Drug Info: {extracted_data}")
        
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        return {"extracted_data": extracted_data, "current_node": "drug_extractor"}
    except Exception as e:
        # 记录错误日志
        logger.error(
            "Drug extractor agent error",
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

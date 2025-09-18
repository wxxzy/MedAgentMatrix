from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from app.utils.llm_utils import get_llm_instance # 导入统一的LLM获取函数

load_dotenv()

class SupplementInfo(BaseModel):
    """保健品信息"""
    approval_number: Optional[str] = Field(description="批准文号 / 备案号 (国食健注/食健备...)")
    product_name: str = Field(description="通用名 / 商品名")
    brand: Optional[str] = Field(description="品牌")
    specification: str = Field(description="规格")
    manufacturer: str = Field(description="生产企业")
    main_ingredients: Optional[str] = Field(description="成分/主要原料")
    execution_standard: Optional[str] = Field(description="执行标准")
    barcode: Optional[str] = Field(description="条形码")

def extract_supplement_info(state):
    """从原始文本中提取保健品信息"""
    print("---SUPPLEMENT EXTRACTOR AGENT---")
    raw_text = state["raw_text"]
    
    llm = get_llm_instance() # 使用统一函数获取LLM实例

    parser = JsonOutputParser(pydantic_object=SupplementInfo)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个保健品信息提取专家。请从提供的商品信息中，严格按照以下JSON Schema提取保健品的相关属性。
        如果某个字段在原文中未提及，请返回空字符串。特别注意批准文号/备案号的格式，如国食健注、食健备等。"""),
        ("human", "{raw_text}\n{format_instructions}")
    ]).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    
    extracted_data = chain.invoke({"raw_text": raw_text})
    
    print(f"Extracted Supplement Info: {extracted_data}")
    return {"extracted_data": extracted_data, "current_node": "supplement_extractor"}

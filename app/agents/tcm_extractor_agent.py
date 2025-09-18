from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from app.utils.llm_utils import get_llm_instance # 导入统一的LLM获取函数

load_dotenv()

class TCMInfo(BaseModel):
    """中药饮片信息"""
    product_name: str = Field(description="品名 (如：当归)")
    brand: Optional[str] = Field(description="品牌")
    specification: str = Field(description="规格")
    manufacturer: str = Field(description="生产企业")
    main_ingredients: Optional[str] = Field(description="药材来源/成分")
    dosage_form: Optional[str] = Field(description="炮制方法/剂型")
    execution_standard: Optional[str] = Field(description="执行标准")
    barcode: Optional[str] = Field(description="条形码")

def extract_tcm_info(state):
    """从原始文本中提取中药饮片信息"""
    print("---TCM EXTRACTOR AGENT---")
    raw_text = state["raw_text"]
    
    llm = get_llm_instance() # 使用统一函数获取LLM实例

    parser = JsonOutputParser(pydantic_object=TCMInfo)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个中药饮片信息提取专家。请从提供的商品信息中，严格按照以下JSON Schema提取中药饮片的相关属性。
        如果某个字段在原文中未提及，请返回空字符串。中药饮片通常只有品名，品牌概念较弱，批准文号不适用。"""),
        ("human", "{raw_text}\n{format_instructions}")
    ]).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    
    extracted_data = chain.invoke({"raw_text": raw_text})
    
    print(f"Extracted TCM Info: {extracted_data}")
    return {"extracted_data": extracted_data, "current_node": "tcm_extractor"}

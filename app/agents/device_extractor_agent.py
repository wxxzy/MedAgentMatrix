from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from app.utils.llm_utils import get_llm_instance # 导入统一的LLM获取函数

load_dotenv()

class DeviceInfo(BaseModel):
    """医疗器械信息"""
    approval_number: str = Field(description="批准文号 / 备案号 (械注准/备案...)")
    product_name: str = Field(description="通用名 / 商品名")
    brand: Optional[str] = Field(description="品牌")
    specification: str = Field(description="规格")
    manufacturer: str = Field(description="生产企业")
    mah: Optional[str] = Field(description="上市许可持有人 (注册人/备案人)")
    product_technical_requirements_number: Optional[str] = Field(description="产品技术要求编号")
    registration_classification: Optional[str] = Field(description="注册分类 (I/II/III类)")
    barcode: Optional[str] = Field(description="条形码")

def extract_device_info(state):
    """从原始文本中提取医疗器械信息"""
    print("---DEVICE EXTRACTOR AGENT---")
    raw_text = state["raw_text"]
    
    llm = get_llm_instance() # 使用统一函数获取LLM实例

    parser = JsonOutputParser(pydantic_object=DeviceInfo)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个医疗器械信息提取专家。请从提供的商品信息中，严格按照以下JSON Schema提取医疗器械的相关属性。
        如果某个字段在原文中未提及，请返回空字符串。特别注意批准文号/备案号的格式，如械注准、械备等。"""),
        ("human", "{raw_text}\n{format_instructions}")
    ]).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    
    extracted_data = chain.invoke({"raw_text": raw_text})
    
    print(f"Extracted Device Info: {extracted_data}")
    return {"extracted_data": extracted_data, "current_node": "device_extractor"}

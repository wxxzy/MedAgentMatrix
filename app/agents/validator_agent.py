from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import json
from app.utils.llm_utils import get_llm_instance # 导入统一的LLM获取函数

load_dotenv()

# 定义LLM输出的Pydantic模型，用于结构化验证结果
class ValidationResult(BaseModel):
    validation_status: str = Field(description="验证状态，'PASSED' 或 'FAILED'")
    review_reason: Optional[str] = Field(description="如果验证失败，提供具体原因")
    validated_data: Optional[Dict[str, Any]] = Field(description="如果验证通过，返回经过验证的数据")

def validate_data(state: Dict[str, Any]) -> Dict[str, Any]:
    print("---VALIDATOR AGENT (Simplified) ---")
    extracted_data = state["extracted_data"]
    product_type = state["product_type"]

    llm = get_llm_instance() # 使用统一函数获取LLM实例
    parser = JsonOutputParser(pydantic_object=ValidationResult)

    # 定义简化的Prompt，依靠LLM自身知识进行判断
    system_message_content = f"""你是一个专业的药品信息验证专家。你的任务是根据提供的商品类型和提取出的商品信息，
    判断这些信息是否合理、完整和符合常识。你不需要调用任何外部工具。
    商品类型为: {product_type}。

    请严格按照以下步骤进行验证：
    1. 检查提取出的关键字段（如产品名称、生产企业、规格、批准文号/注册证号等）是否缺失或明显不合理。
    2. 根据商品类型，判断批准文号/注册证号的格式是否符合该类型商品的常见规范（例如，药品应有国药准字，器械应有械注准等）。
    3. 判断各字段值之间是否存在明显的逻辑冲突或不一致。
    4. 如果验证通过，请返回一个JSON字符串。该JSON字符串必须包含一个键 'validation_status'，值为 'PASSED'，以及一个键 'validated_data'，其值为经过验证的数据（通常与输入相同，除非你进行了标准化）。
    5. 如果验证失败，请返回一个JSON字符串。该JSON字符串必须包含一个键 'validation_status'，值为 'FAILED'，一个键 'review_reason'，值为具体失败原因。
    6. 你的输出必须是严格的JSON格式，不包含任何额外文本或解释。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message_content),
        ("human", f"请验证以下提取出的商品信息：\n{{extracted_data}}") # 添加格式指令
    ])

    validation_chain = prompt | llm | parser

    try:
        # 调用LLM进行验证
        validation_output = validation_chain.invoke({
            "product_type": product_type,
            "extracted_data": json.dumps(extracted_data)
        })
        
        # 确保validation_output是字典，并安全访问键
        if isinstance(validation_output, dict):
            if validation_output.get("validation_status") == "PASSED":
                print("Validation successful.")
                return {"validated_data": validation_output.get("validated_data") or extracted_data, "review_reason": None, "current_node": "validator"}
            else:
                print(f"Validation failed: {validation_output.get('review_reason')}")
                return {"validated_data": extracted_data, "review_reason": validation_output.get('review_reason'), "current_node": "validator"}
        else: # 如果parser成功返回了Pydantic对象
            if validation_output.validation_status == "PASSED":
                print("Validation successful.")
                return {"validated_data": validation_output.validated_data or extracted_data, "review_reason": None, "current_node": "validator"}
            else:
                print(f"Validation failed: {validation_output.review_reason}")
                return {"validated_data": extracted_data, "review_reason": validation_output.review_reason, "current_node": "validator"}

    except Exception as e:
        print(f"Validator Agent执行失败: {e}")
        return {"validated_data": extracted_data, "review_reason": f"Validator Agent执行异常: {e}", "current_node": "validator"}

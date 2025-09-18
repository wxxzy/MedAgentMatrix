from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from app.utils.llm_utils import get_llm_instance # 导入统一的LLM获取函数

load_dotenv()

def get_classifier_chain():
    llm = get_llm_instance() # 使用统一函数获取LLM实例
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个商品分类专家。根据提供的商品信息，判断其最可能的商品类型。类型选项为：[药品, 器械, 药妆, 保健品, 中药饮片, 普通商品]。请重点关注'批准文号'、'注册证号'等关键词。仅返回类型名称，不要包含任何其他文字或解释。如果无法判断，返回'普通商品'。"),
        ("user", "{raw_text}")
    ])
    return prompt | llm

def classify_product(state):
    print("---CLASSIFIER AGENT---")
    raw_text = state["raw_text"]
    classifier_chain = get_classifier_chain()
    product_type = classifier_chain.invoke({"raw_text": raw_text}).content.strip()
    
    product_type = product_type.replace("。", "").replace("：", "").replace(" ", "")
    if product_type not in ["药品", "器械", "药妆", "保健品", "中药饮片", "普通商品"]:
        product_type = "普通商品"

    print(f"Classifier output: '{product_type}'")
    return {"product_type": product_type, "current_node": "classifier"}

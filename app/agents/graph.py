from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, List, Dict, Any
from datetime import datetime
from app.agents.classifier_agent import classify_product
from app.agents.drug_extractor_agent import extract_drug_info
from app.agents.device_extractor_agent import extract_device_info
from app.agents.cosmeceutical_extractor_agent import extract_cosmeceutical_info
from app.agents.supplement_extractor_agent import extract_supplement_info
from app.agents.tcm_extractor_agent import extract_tcm_info
from app.agents.general_extractor_agent import extract_general_info
from app.agents.validator_agent import validate_data
from app.agents.enhanced_matcher_agent import match_product
from app.agents.fusion_agent import fuse_product
from app.agents.human_in_the_loop_agent import request_review
from app.agents.save_product_agent import save_product # Although not in the graph, it's part of the agent system

# 定义Agent History项的结构
class AgentHistoryItem(TypedDict):
    agent_name: str
    output: Dict[str, Any]
    timestamp: datetime

class AgentState(TypedDict):
    raw_text: str
    product_type: str
    extracted_data: dict
    validated_data: dict
    match_result: dict
    fusion_result: dict
    review_reason: str
    review_decision: Literal["APPROVED", "REJECTED"]
    review_id: int
    spu_id: int
    current_node: str
    agent_history: List[AgentHistoryItem] # 新增：记录Agent处理历史

# Graph Definition
workflow = StateGraph(AgentState)

# Define the nodes
workflow.add_node("classifier", classify_product)
workflow.add_node("drug_extractor", extract_drug_info)
workflow.add_node("device_extractor", extract_device_info)
workflow.add_node("cosmeceutical_extractor", extract_cosmeceutical_info)
workflow.add_node("supplement_extractor", extract_supplement_info)
workflow.add_node("tcm_extractor", extract_tcm_info)
workflow.add_node("general_extractor", extract_general_info)
workflow.add_node("validator", validate_data)
workflow.add_node("matcher", match_product)
workflow.add_node("fusion", fuse_product)
workflow.add_node("request_review", request_review)

# Define the edges
workflow.set_entry_point("classifier")

def route_to_extractor(state):
    # ... (routing logic remains the same)
    product_type = state["product_type"]
    if product_type == "药品": return "drug_extractor"
    if product_type == "器械": return "device_extractor"
    if product_type == "药妆": return "cosmeceutical_extractor"
    if product_type == "保健品": return "supplement_extractor"
    if product_type == "中药饮片": return "tcm_extractor"
    if product_type == "普通商品": return "general_extractor"
    return "request_review"

workflow.add_conditional_edges(
    "classifier",
    route_to_extractor,
    {
        "drug_extractor": "drug_extractor",
        "device_extractor": "device_extractor",
        "cosmeceutical_extractor": "cosmeceutical_extractor",
        "supplement_extractor": "supplement_extractor",
        "tcm_extractor": "tcm_extractor",
        "general_extractor": "general_extractor",
        "request_review": "request_review"
    }
)

workflow.add_edge("drug_extractor", "validator")
workflow.add_edge("device_extractor", "validator")
workflow.add_edge("cosmeceutical_extractor", "validator")
workflow.add_edge("supplement_extractor", "validator")
workflow.add_edge("tcm_extractor", "validator")
workflow.add_edge("general_extractor", "validator")

def after_validation(state):
    return "request_review" if state.get("review_reason") else "matcher"

workflow.add_conditional_edges("validator", after_validation, {"matcher": "matcher", "request_review": "request_review"})

def after_matching(state):
    match_status = state.get("match_result", {}).get("status")
    # 如果完全匹配，直接结束流程
    if match_status == "MATCH":
        return END
    # 如果需要人工审核或有候选产品，转到融合节点
    elif match_status in ["HIGH_SIMILARITY", "CANDIDATES"]:
        return "fusion"
    # 如果没有匹配，也需要人工审核
    else:
        return "request_review"

workflow.add_conditional_edges("matcher", after_matching, {"fusion": "fusion", "request_review": "request_review", END: END})

def after_fusion(state):
    fusion_status = state.get("fusion_result", {}).get("status")
    # 如果融合成功，直接保存产品
    if fusion_status == "FUSED":
        # 我们需要将融合后的数据传递给保存代理
        # 这里我们返回一个特殊的值，表示应该保存融合后的数据
        return "SAVE_FUSED_PRODUCT"
    # 如果需要人工审核，转到审核节点
    elif fusion_status == "NEEDS_REVIEW":
        return "request_review"
    # 如果是新产品，也需要人工审核
    else:
        return "request_review"

# 添加融合节点的条件边
workflow.add_conditional_edges("fusion", after_fusion, {"SAVE_FUSED_PRODUCT": "save_fused_product", "request_review": "request_review"})

# 添加一个特殊的节点来处理融合后的产品保存
def save_fused_product(state):
    # 从融合结果中获取数据
    fusion_result = state.get("fusion_result", {})
    fused_data = fusion_result.get("fused_data", {})
    spu_id = fusion_result.get("spu_id")
    
    # 构造传递给保存代理的状态
    save_state = {
        "product_type": state.get("product_type"),
        "validated_data": fused_data,
        "spu_id": spu_id,
        "current_node": "save_product"
    }
    
    # 调用保存代理
    from app.agents.save_product_agent import save_product
    result = save_product(save_state)
    
    # 返回结果，结束流程
    return result

# 添加保存融合产品的节点
workflow.add_node("save_fused_product", save_fused_product)

# 添加从保存融合产品节点到结束的边
workflow.add_edge("save_fused_product", END)

# request_review is now a terminal node for this workflow.
workflow.add_edge("request_review", END)

# Compile the graph
agent_executor = workflow.compile()

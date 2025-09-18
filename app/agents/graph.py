from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from app.agents.classifier_agent import classify_product
from app.agents.drug_extractor_agent import extract_drug_info
from app.agents.device_extractor_agent import extract_device_info
from app.agents.cosmeceutical_extractor_agent import extract_cosmeceutical_info
from app.agents.supplement_extractor_agent import extract_supplement_info
from app.agents.tcm_extractor_agent import extract_tcm_info
from app.agents.general_extractor_agent import extract_general_info
from app.agents.validator_agent import validate_data
from app.agents.matcher_agent import match_product
from app.agents.human_in_the_loop_agent import request_review
from app.agents.save_product_agent import save_product # Although not in the graph, it's part of the agent system

class AgentState(TypedDict):
    raw_text: str
    product_type: str
    extracted_data: dict
    validated_data: dict
    match_result: dict
    review_reason: str
    review_decision: Literal["APPROVED", "REJECTED"]
    review_id: int
    spu_id: int
    current_node: str

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
    return "request_review" if state.get("match_result", {}).get("status") != "MATCH" else END

workflow.add_conditional_edges("matcher", after_matching, {"request_review": "request_review", END: END})

# request_review is now a terminal node for this workflow.
workflow.add_edge("request_review", END)

# Compile the graph
agent_executor = workflow.compile()

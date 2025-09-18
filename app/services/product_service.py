from app.agents.graph import agent_executor, AgentState
from app.agents.save_product_agent import save_product
import traceback
from app.socket import sio
from typing import Dict, Any
import copy

async def process_product_task(raw_text: str, task_id: str, tasks: Dict, sid: str = None):
    print(f"[ProductService] Starting process for task_id: {task_id}")
    
    initial_state = {"raw_text": raw_text, "current_node": "__start__"}
    tasks[task_id]["status"] = "PROCESSING"
    tasks[task_id]["history"] = []
    current_state = copy.deepcopy(initial_state)

    try:
        async for step in agent_executor.astream(initial_state):
            node_output = list(step.values())[0]
            current_state.update(node_output)
            node_name = current_state.get("current_node", "unknown_node")

            print(f"[ProductService] Agent yielded step: {node_name} for task_id {task_id}")

            frontend_payload = {"node": node_name, "state": current_state}
            tasks[task_id]["history"].append(frontend_payload)

            if sid:
                await sio.emit('agent_step', frontend_payload, room=sid)

        final_state = current_state
        print(f"[ProductService] Agent executor finished for task_id: {task_id}")
        
        tasks[task_id]["result"] = final_state
        if final_state.get("review_reason"):
            tasks[task_id]["status"] = "NEEDS_REVIEW"
        else:
            tasks[task_id]["status"] = "COMPLETED"

    except Exception as e:
        error_message = traceback.format_exc()
        print(f"[ProductService] Error processing task {task_id}: {e}")
        tasks[task_id]["status"] = "FAILED"
        tasks[task_id]["error"] = error_message
        error_payload = {"node": "error", "state": {"error": str(e), "traceback": error_message}}
        tasks[task_id]["history"].append(error_payload)
        if sid:
            await sio.emit("agent_step", error_payload, room=sid)

async def save_approved_product_task(state: Dict[str, Any], task_id: str, tasks: Dict, sid: str = None):
    """A simple task to call the save_product agent and notify the client."""
    print(f"[ProductService] Starting save_approved_product_task for task_id: {task_id}")
    tasks[task_id]["status"] = "SAVING_APPROVED_PRODUCT"
    
    try:
        # Directly call the save_product function, which is now outside the graph
        save_result = save_product(state)
        
        current_state = {**state, **save_result}
        node_name = current_state.get("current_node", "unknown_node") # Should be 'save_product'

        print(f"[ProductService] Save result: {save_result}")

        frontend_payload = {"node": node_name, "state": current_state}
        tasks[task_id]["history"].append(frontend_payload)
        tasks[task_id]["status"] = "COMPLETED_FROM_REVIEW"
        tasks[task_id]["result"] = current_state

        if sid:
            await sio.emit('agent_step', frontend_payload, room=sid)

    except Exception as e:
        error_message = traceback.format_exc()
        print(f"[ProductService] Error in save_approved_product_task {task_id}: {e}")
        tasks[task_id]["status"] = "FAILED_FROM_REVIEW"
        tasks[task_id]["error"] = error_message
        error_payload = {"node": "error", "state": {"error": str(e), "traceback": error_message}}
        tasks[task_id]["history"].append(error_payload)
        if sid:
            await sio.emit("agent_step", error_payload, room=sid)
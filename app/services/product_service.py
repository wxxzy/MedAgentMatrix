import time
import traceback
from typing import Dict, Any
import copy
from datetime import datetime
from app.agents.graph import agent_executor, AgentState
from app.agents.save_product_agent import save_product
from app.socket import sio
from app.utils.logging_config import get_logger, TASK_PROCESSED, TASK_DURATION

# 初始化日志记录器
logger = get_logger(__name__)

async def process_product_task(raw_text: str, task_id: str, tasks: Dict, sid: str = None):
    start_time = time.time()
    # 记录开始处理任务的日志
    logger.info(f"[ProductService] Starting process for task_id: {task_id}")
    
    initial_state = {"raw_text": raw_text, "current_node": "__start__", "agent_history": []}
    tasks[task_id]["status"] = "PROCESSING"
    tasks[task_id]["history"] = []
    current_state = copy.deepcopy(initial_state)

    try:
        async for step in agent_executor.astream(initial_state):
            node_output = list(step.values())[0]
            current_state.update(node_output)
            node_name = current_state.get("current_node", "unknown_node")
            
            # 记录Agent处理历史
            agent_history_item = {
                "agent_name": node_name,
                "output": node_output,
                "timestamp": datetime.now()
            }
            current_state["agent_history"].append(agent_history_item)

            # 记录Agent执行步骤的日志
            logger.info(f"[ProductService] Agent yielded step: {node_name} for task_id {task_id}")

            frontend_payload = {"node": node_name, "state": current_state}
            tasks[task_id]["history"].append(frontend_payload)

            if sid:
                await sio.emit('agent_step', frontend_payload, room=sid)

        final_state = current_state
        # 记录Agent执行器完成的日志
        logger.info(f"[ProductService] Agent executor finished for task_id: {task_id}")
        
        tasks[task_id]["result"] = final_state
        if final_state.get("review_reason"):
            tasks[task_id]["status"] = "NEEDS_REVIEW"
        else:
            tasks[task_id]["status"] = "COMPLETED"
            
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)

    except Exception as e:
        error_message = traceback.format_exc()
        # 记录处理任务错误的日志
        logger.error(f"[ProductService] Error processing task {task_id}: {e}")
        tasks[task_id]["status"] = "FAILED"
        tasks[task_id]["error"] = error_message
        error_payload = {"node": "error", "state": {"error": str(e), "traceback": error_message}}
        tasks[task_id]["history"].append(error_payload)
        if sid:
            await sio.emit("agent_step", error_payload, room=sid)
            
        # 更新监控指标
        TASK_PROCESSED.labels(status="error").inc()
        TASK_DURATION.observe(time.time() - start_time)

async def save_approved_product_task(state: Dict[str, Any], task_id: str, tasks: Dict, sid: str = None):
    """调用save_product agent并通知客户端的简单任务"""
    start_time = time.time()
    # 记录开始保存审核通过产品的任务日志
    logger.info(f"[ProductService] Starting save_approved_product_task for task_id: {task_id}")
    tasks[task_id]["status"] = "SAVING_APPROVED_PRODUCT"
    
    try:
        # 直接调用save_product函数，它现在在图之外
        save_result = save_product(state)
        
        current_state = {**state, **save_result}
        node_name = current_state.get("current_node", "unknown_node") # 应该是 'save_product'

        # 记录保存结果的日志
        logger.info(f"[ProductService] Save result: {save_result}")

        frontend_payload = {"node": node_name, "state": current_state}
        tasks[task_id]["history"].append(frontend_payload)
        tasks[task_id]["status"] = "COMPLETED_FROM_REVIEW"
        tasks[task_id]["result"] = current_state

        if sid:
            await sio.emit('agent_step', frontend_payload, room=sid)
            
        # 更新监控指标
        TASK_PROCESSED.labels(status="success").inc()
        TASK_DURATION.observe(time.time() - start_time)

    except Exception as e:
        error_message = traceback.format_exc()
        # 记录保存审核通过产品任务错误的日志
        logger.error(f"[ProductService] Error in save_approved_product_task {task_id}: {e}")
        tasks[task_id]["status"] = "FAILED_FROM_REVIEW"
        tasks[task_id]["error"] = error_message
        error_payload = {"node": "error", "state": {"error": str(e), "traceback": error_message}}
        tasks[task_id]["history"].append(error_payload)
        if sid:
            await sio.emit("agent_step", error_payload, room=sid)
            
        # 更新监控指标
        TASK_PROCESSED.labels(status="error").inc()
        TASK_DURATION.observe(time.time() - start_time)
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.product_service import process_product_task, save_approved_product_task
from app.models.schema import ReviewQueue, MasterProduct, ProcessRequest
from app.database import SessionLocal
from app.agents.graph import AgentState
import uuid
import json

router = APIRouter()

tasks = {}

@router.post("/products/process")
async def process_product(request: ProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "PROCESSING", "history": []}
    background_tasks.add_task(process_product_task, request.raw_text, task_id, tasks, request.sid)
    return {"task_id": task_id, "status": "PROCESSING"}

@router.get("/products/status/{task_id}")
def get_status(task_id: str):
    task_info = tasks.get(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_info

@router.get("/products/review/queue")
def get_review_queue():
    db = SessionLocal()
    try:
        items = db.query(ReviewQueue).filter(ReviewQueue.status == 'PENDING').all()
        return items
    finally:
        db.close()

@router.post("/products/review/submit/{review_id}")
async def submit_review(review_id: int, approved: bool, background_tasks: BackgroundTasks, sid: str = None):
    db = SessionLocal()
    try:
        item = db.query(ReviewQueue).filter(ReviewQueue.review_id == review_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Review item not found")
        if item.status != 'PENDING':
            raise HTTPException(status_code=400, detail=f"Review item has already been processed with status: {item.status}")

        decision = "APPROVED" if approved else "REJECTED"
        item.status = decision
        db.commit()

        if approved:
            # Prepare the state for the save_product agent
            state_to_save = {
                "product_type": item.product_type,
                "validated_data": json.loads(item.validated_data),
                "current_node": "save_product" # Explicitly set the current node
            }
            
            task_id = str(uuid.uuid4())
            tasks[task_id] = {"status": f"SAVING_APPROVED_PRODUCT", "history": [] }
            
            # Call the new, dedicated service task
            background_tasks.add_task(save_approved_product_task, state_to_save, task_id, tasks, sid)
            return {"status": "SUCCESS", "review_id": review_id, "new_status": decision, "continuation_task_id": task_id}
        else:
            # If rejected, just update the status and do nothing else
            return {"status": "SUCCESS", "review_id": review_id, "new_status": decision}

    finally:
        db.close()

@router.get("/products")
def get_all_products():
    db = SessionLocal()
    try:
        products = db.query(MasterProduct).all()
        return products
    finally:
        db.close()
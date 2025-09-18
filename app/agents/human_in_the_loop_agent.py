from app.database import SessionLocal
from app.models.schema import ReviewQueue
import json

def request_review(state):
    """Saves the data to the review queue in the database and pauses the workflow."""
    print("---HUMAN IN THE LOOP AGENT---")
    reason = state.get("review_reason", "未知原因，需要人工审核。")
    
    db = SessionLocal()
    try:
        review_item = ReviewQueue(
            raw_info=json.dumps({"raw_text": state.get("raw_text")}),
            extracted_data=json.dumps(state.get("extracted_data", {})),
            validated_data=json.dumps(state.get("validated_data", {})),
            product_type=state.get("product_type"),
            review_reason=reason,
            status="PENDING"
        )
        db.add(review_item)
        db.commit()
        db.refresh(review_item)
        review_id = review_item.review_id
        print(f"Saved item to review queue with ID: {review_id}")
        return {"review_id": review_id, "review_reason": reason, "current_node": "request_review"}
    finally:
        db.close()

from app.database import SessionLocal
from app.models.schema import MasterProduct

def match_product(state):
    print("---MATCHER AGENT---")
    db = SessionLocal()
    try:
        validated_data = state.get("validated_data", {})
        approval_number = validated_data.get("approval_number")
        
        match_result = {"status": "NO_MATCH", "spu_id": None}

        if approval_number:
            print(f"Attempting to match by approval number: {approval_number}")
            product = db.query(MasterProduct).filter(MasterProduct.approval_number == approval_number).first()
            if product:
                print(f"Match found for approval number {approval_number}. SPU ID: {product.spu_id}")
                match_result = {"status": "MATCH", "spu_id": product.spu_id}
            else:
                print(f"No match found for approval number: {approval_number}")
        else:
            print("No approval number provided, skipping match.")

        return {"match_result": match_result, "current_node": "matcher"}
    finally:
        db.close()

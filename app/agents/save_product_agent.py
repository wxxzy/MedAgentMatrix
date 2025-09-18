from app.database import SessionLocal
from app.models.schema import MasterProduct

def save_product(state):
    """Saves the validated product data to the master_products table."""
    print("---SAVE PRODUCT AGENT---")
    validated_data = state.get("validated_data")
    product_type = state.get("product_type")

    if not validated_data or not product_type:
        print("Error: Cannot save product, validated_data or product_type is missing.")
        return {"error": "Cannot save product, validated_data or product_type is missing.", "current_node": "save_product"}

    db = SessionLocal()
    try:
        new_product = MasterProduct(
            product_type=product_type,
            product_name=validated_data.get("product_name"),
            brand=validated_data.get("brand"),
            manufacturer=validated_data.get("manufacturer"),
            approval_number=validated_data.get("approval_number"),
            specification=validated_data.get("specification"),
            barcode=validated_data.get("barcode"),
            mah=validated_data.get("mah"),
            dosage_form=validated_data.get("dosage_form"),
            product_technical_requirements_number=validated_data.get("product_technical_requirements_number"),
            registration_classification=validated_data.get("registration_classification"),
            main_ingredients=validated_data.get("main_ingredients"),
            execution_standard=validated_data.get("execution_standard")
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        spu_id = new_product.spu_id
        print(f"Successfully saved new product with SPU ID: {spu_id}")
        return {"spu_id": spu_id, "current_node": "save_product"}
    except Exception as e:
        print(f"Error saving product to database: {e}")
        db.rollback()
        return {"error": str(e), "current_node": "save_product"}
    finally:
        db.close()

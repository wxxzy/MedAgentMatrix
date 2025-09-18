import random

def query_nmpa(approval_number: str) -> dict:
    """Simulates a query to the NMPA database."""
    print(f"Querying NMPA for: {approval_number}")
    # In a real scenario, this would involve an API call or web scraping.
    # For this MVP, we'll simulate the result.
    if not approval_number or "H" not in approval_number:
        return {"status": "INVALID_FORMAT", "data": None}
    
    # Simulate a small chance of not finding a valid number
    if random.random() < 0.1:
        return {"status": "NOT_FOUND", "data": None}
    
    return {
        "status": "FOUND",
        "data": {
            "approval_number": approval_number,
            "product_name": "模拟药品名称",
            "manufacturer": "模拟生产厂家"
        }
    }

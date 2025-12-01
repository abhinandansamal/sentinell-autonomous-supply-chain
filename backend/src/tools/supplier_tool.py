import os
import requests
import json
from mcp.server.fastmcp import FastMCP
from src.utils.logger import setup_logger

logger = setup_logger("tool_supplier")
mcp = FastMCP("Sentinell_Procurement")

# In Cloud Run, everything runs on the PORT env var (default 8080).
# Since we mounted the supplier at "/supplier", we access it via localhost:8080
# DYNAMIC CONFIGURATION
# We grab the same PORT the server is running on.
PORT = os.getenv("PORT", "8080") 
SUPPLIER_API_URL = f"http://127.0.0.1:{PORT}/supplier/v1/order"

@mcp.tool()
def get_price_quote(part_name: str, quantity: int, urgent: bool = False) -> str:
    """
    Gets a price estimate from the supplier WITHOUT placing an order.
    Use this to check costs before committing to a purchase.
    
    Args:
        part_name (str): The SKU name.
        quantity (int): Number of units.
        urgent (bool): Shipping urgency.
        
    Returns:
        str: JSON string containing the estimated total cost.
    """
    # For this mock, we simulate the same pricing logic as the server
    # In a real app, we would hit a GET /quote endpoint
    base_price = 50.0
    shipping = 500.0 if urgent else 100.0
    estimated_total = (quantity * base_price) + shipping
    
    logger.info(f"💲 Quote requested: {quantity}x{part_name} = ${estimated_total}")
    return json.dumps({"estimated_cost": estimated_total, "currency": "USD"})

@mcp.tool()
def order_parts_from_supplier(part_name: str, quantity: int, urgent: bool = False) -> str:
    """
    Sends a purchase order to an external supplier via the A2A (Agent-to-Agent) protocol.
    
    Use this tool when you need to replenish stock for a critical item.

    Args:
        part_name (str): The SKU or name of the part (e.g., 'Logic-Core-CPU-X1').
        quantity (int): Number of units to order.
        urgent (bool): Set to True if the risk level is CRITICAL and speed is required.

    Returns:
        str: A summary of the order status (Confirmed or Rejected) and the cost.
    """
    logger.info(f"🛒 Agent placing order: {quantity} x {part_name} (Urgent={urgent})")
    
    payload = {
        "part_name": part_name,
        "quantity": quantity,
        "urgent": urgent
    }
    
    try:
        # 1. Execute the A2A Call (HTTP POST)
        response = requests.post(SUPPLIER_API_URL, json=payload, timeout=5)
        response.raise_for_status() # Raise error if HTTP 400/500
        
        data = response.json()
        
        # 2. Parse the Response
        order_id = data.get("order_id")
        status = data.get("status")
        cost = data.get("total_cost")
        msg = data.get("message")
        
        if status == "CONFIRMED":
            result = f"✅ ORDER SUCCESS: {order_id}. Cost: ${cost}. ETA: {msg}"
            logger.info(result)
            return result
        else:
            result = f"❌ ORDER REJECTED: Supplier says '{msg}'"
            logger.warning(result)
            return result

    except requests.exceptions.ConnectionError:
        err = "❌ Connection Failed: The internal Supplier Service is unreachable."
        logger.error(err)
        return err
    except Exception as e:
        err = f"❌ Order Failed: {str(e)}"
        logger.error(err)
        return err

if __name__ == "__main__":
    # Test the tool manually
    # Note: Ensure mock_supplier.py is running in another terminal!
    print("🧪 Testing Supplier Tool...")
    print(order_parts_from_supplier("Test-CPU", 5, True))
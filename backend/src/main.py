import os
import uvicorn
import datetime
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from src.utils.telemetry import setup_telemetry
from src.config import settings
from src.utils.logger import setup_logger
from src.agents.watchtower import WatchtowerAgent
from src.agents.procurement import ProcurementAgent
from src.api.models import ScanRequest, ScanResponse, PurchaseRequest, PurchaseResponse
from src.a2a.mock_supplier import app as supplier_app

# Initialize module-level logger
logger = setup_logger("api_server")

# Initialize Observability (Tracer)
# This sets up the OpenTelemetry pipeline before the app starts.
# It allows us to create custom 'Spans' to track specific blocks of code.
tracer = setup_telemetry("sentinell-backend")

# Global State Container
# We use a dictionary to hold agent instances so they persist across requests
# but are initialized only once during the application startup.
agent_registry: Dict[str, Any] = {
    "watchtower": None,
    "procurement": None
}

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the lifecycle of the FastAPI application.

    This context manager replaces the deprecated `@app.on_event("startup")` pattern.
    It handles the heavy lifting of initializing AI Agents (which load models into memory)
    before the server starts accepting traffic.

    Args:
        app (FastAPI): The application instance.

    Yields:
        None: Yields control to the application to start serving requests.
    """
    global agent_registry
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} Backend v{settings.VERSION}...")
    
    try:
        # Create a trace span for the startup process to measure initialization latency
        with tracer.start_as_current_span("startup_initialization"):
            # 1. Initialize Watchtower Agent
            logger.debug("Initializing Watchtower Agent (Risk Monitor)...")
            agent_registry["watchtower"] = WatchtowerAgent()
            
            # 2. Initialize Procurement Agent
            logger.debug("Initializing Procurement Agent (Buyer)...")
            agent_registry["procurement"] = ProcurementAgent()
            
        logger.info("✅ All Agents initialized successfully and ready for duty.")
    
    except Exception as e:
        logger.critical(f"❌ Critical Failure during Agent startup: {e}")
        # Re-raise exception to prevent the server from starting in a broken state
        raise e
    
    yield  # Application runs here
    
    # --- Shutdown Logic ---
    logger.info("🛑 Shutting down Sentinell Backend...")
    agent_registry.clear()

# Create the FastAPI App with Lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for Sentinell.ai - Autonomous Supply Chain Resilience System",
    lifespan=lifespan
)

# Mount the supplier app
# This makes the supplier accessible at http://localhost:8080/supplier
app.mount("/supplier", supplier_app)

# Configure CORS (Cross-Origin Resource Sharing)
# Required to allow the Frontend (running on a different port/domain) to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domain list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTO-INSTRUMENTATION ---
# This line automatically adds tracing to every HTTP endpoint defined in the app.
# It captures details like HTTP Method, Status Code, and Latency automatically.
FastAPIInstrumentor.instrument_app(app)

# --- ENDPOINTS ---

@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, str]:
    """
    Performs a lightweight health check of the API server.
    
    Returns:
        Dict[str, str]: Status status and version info.
    """
    return {"status": "healthy", "version": settings.VERSION}

@app.post("/api/scan", response_model=ScanResponse, tags=["Watchtower"])
async def trigger_scan(request: ScanRequest) -> ScanResponse:
    """
    Triggers a proactive risk scan using the Watchtower Agent.

    This endpoint initiates the 'Loop' agent workflow:
    1. Compresses context from news search.
    2. Analyzes risks (Political/Weather).
    3. Queries internal inventory database.
    
    Args:
        request (ScanRequest): Input payload containing target 'region'.

    Returns:
        ScanResponse: The risk assessment report.
    """
    agent = agent_registry.get("watchtower")
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Watchtower Agent not initialized"
        )
    
    logger.info(f"📨 Scan Request received for region: {request.region}")
    
    # Create a custom span to track the specific logic of the Agent execution
    with tracer.start_as_current_span("agent_scan_execution"):
        try:
            # Execute the ReAct Loop
            report_text = agent.scan_region(request.region)
            
            # Simple heuristic to determine Risk Badge for UI
            risk_level = "LOW"
            upper_text = report_text.upper()
            if "CRITICAL" in upper_text or "HIGH" in upper_text:
                risk_level = "CRITICAL"
            elif "MEDIUM" in upper_text:
                risk_level = "MEDIUM"
                
            return ScanResponse(
                region=request.region,
                risk_level=risk_level,
                summary=report_text,
                timestamp=datetime.datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/purchase", response_model=PurchaseResponse, tags=["Procurement"])
async def trigger_purchase(request: PurchaseRequest) -> PurchaseResponse:
    """
    Triggers the Procurement Agent to execute a purchase order.

    This endpoint initiates the 'Sequential' agent workflow:
    1. Checks Long-Term Memory for supplier reliability.
    2. Checks Price Quote (Tools).
    3. Pauses for Approval if cost > threshold (Human-in-the-loop).
    4. Executes Purchase via A2A Protocol.

    Args:
        request (PurchaseRequest): Input payload containing part, quantity, and risk profile.

    Returns:
        PurchaseResponse: The transaction status and summary.
    """
    agent = agent_registry.get("procurement")
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Procurement Agent not initialized"
        )
    
    logger.info(f"📨 Purchase Request: {request.quantity} x {request.part_name}")
    
    with tracer.start_as_current_span("agent_purchase_execution"):
        try:
            # Execute the Procurement Workflow
            report_text = agent.create_order(
                request.part_name, 
                request.quantity, 
                request.risk_level
            )
            
            # Determine status based on agent output
            status_msg = "COMPLETED" if "ORDER SUCCESS" in report_text else "PENDING/FAILED"
            if "PAUSED" in report_text:
                status_msg = "PAUSED_FOR_APPROVAL"
            
            return PurchaseResponse(
                status=status_msg,
                summary=report_text,
                timestamp=datetime.datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Purchase failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get port from environment or default to 8080 (Cloud Run standard)
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Starting server on port {port}...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import json
import io
import os
from datetime import date, datetime, timedelta
import bcrypt
import jwt

from aws_scanner import scan_region
from aws_client import run_aws, AWSCLIError, AWSCredentialsError, AWSPermissionError, CommandTimeoutError
from cost_intelligence import (
    get_current_cost,
    get_previous_month_cost,
    get_forecast,
    get_top_resources,
    get_anomalies,
)
from budget_engine import set_budget, get_budget as get_budget_summary, get_all_budgets
from ai_analyzer import analyze_resources
from db import (
    db, create_analysis, get_analyses, get_analysis, get_cost_snapshots,
    upsert_cost_snapshot, get_user_by_email, claim_budget_alert, release_budget_alert,
)
from ws_manager import progress_manager
from report_generator import generate_pdf, generate_csv
from email_alerts import send_budget_alert, smtp_configured


class AnalyzeRequest(BaseModel):
    region: str


class BudgetRequest(BaseModel):
    region: str
    monthly_budget: float
    alert_threshold_percent: float = 80.0


class AuthRequest(BaseModel):
    email: str
    password: str


async def _send_budget_alert_if_needed(summary: Dict[str, Any], region: str, user: Dict[str, Any]) -> None:
    status = summary.get("status")
    if status not in ("warning", "exceeded") or not db.pool or not smtp_configured():
        return
    period = date.today().strftime("%Y-%m")
    normalized_region = region.strip()
    if await claim_budget_alert(user["id"], normalized_region, period, status):
        try:
            await send_budget_alert(user["email"], normalized_region, status, summary)
        except Exception:
            await release_budget_alert(user["id"], normalized_region, period, status)
            raise HTTPException(status_code=502, detail="Budget status updated, but the alert email could not be sent.")


JWT_SECRET = os.getenv("JWT_SECRET", "change-this-development-secret")
JWT_ALGORITHM = "HS256"


def _create_token(user: Dict[str, Any]) -> str:
    return jwt.encode(
        {
            "sub": str(user["id"]),
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(hours=24),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"id": int(payload["sub"]), "email": str(payload.get("email", ""))}
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token is required")
    token = authorization.split(" ", 1)[1].strip()
    return _decode_token(token)


app = FastAPI(title="AI Cloud Cost Detective - Resource Discovery & Cost Intelligence")

# Enable CORS for local frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        await db.connect()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Continuing with limited functionality (no persistence).")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    await db.disconnect()


@app.post("/api/auth/signup")
async def signup(payload: AuthRequest):
    email = payload.email.strip().lower()
    if not email or len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="A valid email and password of at least 8 characters are required")
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    if await get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    password_hash = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email",
            email,
            password_hash,
        )
    user_data = dict(user)
    return {"access_token": _create_token(user_data), "token_type": "bearer", "user": user_data}


@app.post("/api/auth/login")
async def login(payload: AuthRequest):
    email = payload.email.strip().lower()
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    user = await get_user_by_email(email)
    if not user or not bcrypt.checkpw(payload.password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {
        "access_token": _create_token(user),
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"]},
    }


@app.get("/api/regions", response_model=List[str])
def list_regions(user: Dict[str, Any] = Depends(current_user)):
    try:
        parsed, _ = run_aws(["ec2", "describe-regions", "--all-regions", "--output", "json"], timeout=20)
    except AWSCredentialsError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except AWSCLIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    regions = []
    try:
        regions_data = parsed.get("Regions", []) if isinstance(parsed, dict) else []
        for r in regions_data:
            name = r.get("RegionName")
            opt_in_status = r.get("OptInStatus")
            if name and opt_in_status in (None, "opt-in-not-required", "opted-in"):
                regions.append(name)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse regions from AWS CLI output.")

    return regions


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest, user: Dict[str, Any] = Depends(current_user)):
    """
    Run comprehensive resource analysis with AI recommendations.
    Returns analysis_id for progress tracking via WebSocket.
    """
    region = req.region
    if not region:
        raise HTTPException(status_code=400, detail="region is required")

    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())
    user_id = user["id"]

    try:
        # Stage 1: Scan active services
        await progress_manager.broadcast(analysis_id, "Querying AWS Cost Explorer for active services...")
        
        # Stage 2: Scan resources
        await progress_manager.broadcast(analysis_id, f"Scanning active services in {region}...")
        inventory = scan_region(region)
        resources = inventory.get("resources", [])
        
        # Stage 3: Get top resources by cost
        await progress_manager.broadcast(analysis_id, "Ranking top cost-driving resources...")
        top_resources = get_top_resources(region, limit=20)
        
        # Stage 4: Compile cost summary (current, previous, forecast, anomalies)
        await progress_manager.broadcast(analysis_id, "Checking budget status...")
        current_cost_data = get_current_cost(region)
        previous_cost_data = get_previous_month_cost(region)
        forecast_data = get_forecast(region, days=15)
        anomalies_data = get_anomalies(region)
        
        cost_summary = {
            "current": current_cost_data,
            "previous_month": previous_cost_data,
            "forecast": forecast_data,
            "top_resources": top_resources,
            "anomalies": anomalies_data,
        }
        
        # Store daily cost snapshot
        stored_analysis_id = None
        if db.pool:
            try:
                current_total = float(current_cost_data.get("total", 0.0))
                await upsert_cost_snapshot(user_id, region, date.today(), current_total)
            except Exception:
                pass  # Silently fail if DB not available
        
        # Stage 5: Run AI analysis
        await progress_manager.broadcast(analysis_id, "Running AI optimization analysis...")
        ai_analysis = analyze_resources(resources, top_resources, region)
        
        # Stage 6: Store results in database
        await progress_manager.broadcast(analysis_id, "Storing results...")
        if db.pool:
            try:
                issues_found = len(ai_analysis.get("issues", []))
                estimated_savings = float(ai_analysis.get("total_estimated_monthly_savings", 0.0))
                stored_analysis_id = await create_analysis(
                    user_id,
                    region,
                    len(resources),
                    issues_found,
                    estimated_savings,
                    cost_summary,
                    ai_analysis,
                )
            except Exception:
                pass  # Silently fail if DB not available

        result = {
            "analysis_id": stored_analysis_id or analysis_id,
            "progress_id": analysis_id,
            "region": region,
            "inventory": inventory,
            "cost_summary": cost_summary,
            "ai_analysis": ai_analysis,
        }
        
        # Stage 7: Complete
        await progress_manager.broadcast(analysis_id, "Analysis complete")
        
    except AWSCredentialsError as e:
        await progress_manager.broadcast(analysis_id, f"Error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except AWSPermissionError as e:
        await progress_manager.broadcast(analysis_id, f"Error: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except CommandTimeoutError as e:
        await progress_manager.broadcast(analysis_id, f"Error: {str(e)}")
        raise HTTPException(status_code=504, detail=str(e))
    except AWSCLIError as e:
        await progress_manager.broadcast(analysis_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await progress_manager.broadcast(analysis_id, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    return result


# Cost intelligence endpoints
@app.get("/api/cost/current")
def api_current_cost(region: str = Query(..., description="AWS region to query"), user: Dict[str, Any] = Depends(current_user)):
    try:
        return get_current_cost(region)
    except AWSCredentialsError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except AWSCLIError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/previous-month")
def api_previous_month_cost(region: str = Query(..., description="AWS region to query"), user: Dict[str, Any] = Depends(current_user)):
    try:
        return get_previous_month_cost(region)
    except AWSCredentialsError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except AWSCLIError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/forecast")
def api_forecast(region: str = Query(..., description="AWS region to query"), days: int = Query(15, ge=1, le=90), user: Dict[str, Any] = Depends(current_user)):
    try:
        return get_forecast(region, days=days)
    except AWSCredentialsError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except AWSCLIError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/top-resources")
def api_top_resources(region: str = Query(..., description="AWS region to query"), limit: int = Query(10, ge=1, le=10), user: Dict[str, Any] = Depends(current_user)):
    try:
        return get_top_resources(region, limit=limit)
    except AWSCredentialsError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except AWSCLIError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/anomalies")
def api_anomalies(region: str = Query(..., description="AWS region to query"), threshold: float = Query(0.2, ge=0.0, le=1.0), user: Dict[str, Any] = Depends(current_user)):
    try:
        return get_anomalies(region, threshold=threshold)
    except AWSCredentialsError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except AWSCLIError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/budget")
async def api_create_budget(payload: BudgetRequest, user: Dict[str, Any] = Depends(current_user)):
    try:
        summary = set_budget(payload.region, payload.monthly_budget, payload.alert_threshold_percent, user_id=user["id"])
        await _send_budget_alert_if_needed(summary, payload.region, user)
        return summary
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except AWSCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AWSPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AWSCLIError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/budget")
async def api_get_budget(region: str = Query(..., description="AWS region to query"), user: Dict[str, Any] = Depends(current_user)):
    result = get_budget_summary(region, user_id=user["id"])
    if result.get("configured"):
        await _send_budget_alert_if_needed(result, region, user)
    return result


@app.get("/api/budget/all")
def api_get_all_budgets(user: Dict[str, Any] = Depends(current_user)):
    return get_all_budgets(user_id=user["id"])


# History and WebSocket endpoints
@app.get("/api/history")
async def api_get_history(limit: int = Query(50, ge=1, le=100), user: Dict[str, Any] = Depends(current_user)):
    """Get past analyses for the current user."""
    user_id = user["id"]
    if not db.pool:
        return {"available": False, "reason": "Database not available"}
    
    try:
        analyses = await get_analyses(user_id, limit=limit)
        return {"available": True, "analyses": analyses}
    except Exception as e:
        return {"available": False, "reason": str(e)}


@app.get("/api/cost/history")
async def api_cost_history(region: str = Query(..., description="AWS region to query"), days: int = Query(90, ge=1, le=365), user: Dict[str, Any] = Depends(current_user)):
    """Get stored daily cost snapshots for a region."""
    user_id = user["id"]
    if not db.pool:
        return {"available": False, "snapshots": [], "reason": "Database not available"}
    
    try:
        snapshots = await get_cost_snapshots(user_id, region, days=days)
        return {"available": True, "snapshots": snapshots}
    except Exception as e:
        return {"available": False, "snapshots": [], "reason": str(e)}


@app.websocket("/ws/progress/{analysis_id}")
async def websocket_progress(websocket: WebSocket, analysis_id: str):
    """WebSocket endpoint for real-time progress tracking during analysis."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    try:
        _decode_token(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return
    await progress_manager.connect(analysis_id, websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages (not used for now)
            data = await websocket.receive_text()
            # Could implement control messages here if needed
    except WebSocketDisconnect:
        await progress_manager.disconnect(analysis_id, websocket)


@app.get("/api/report/{analysis_id}/download")
async def download_report(analysis_id: int, format: str = Query("pdf", pattern="^(pdf|csv)$"), user: Dict[str, Any] = Depends(current_user)):
    """
    Download a completed analysis report in PDF or CSV format.
    
    Args:
        analysis_id: ID of the analysis to download
        format: Export format ("pdf" or "csv")
    
    Returns:
        File response with appropriate content type and filename
    """
    user_id = user["id"]
    
    # Retrieve the analysis
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        analysis = await get_analysis(user_id, analysis_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    
    region = analysis.get("region", "unknown")
    created_at = analysis.get("created_at", date.today())
    
    # Format filename with region and date
    if isinstance(created_at, str):
        date_str = created_at.split("T")[0]  # Extract date part from ISO format
    else:
        date_str = created_at.strftime("%Y-%m-%d")
    
    filename = f"cost-report-{region}-{date_str}"
    
    if format == "pdf":
        # Generate PDF
        pdf_buffer = io.BytesIO()
        generate_pdf(analysis, pdf_buffer)
        pdf_buffer.seek(0)
        
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    
    elif format == "csv":
        # Generate CSV
        csv_buffer = io.StringIO()
        generate_csv(analysis, csv_buffer)
        csv_content = csv_buffer.getvalue()
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )


@app.get("/api/report/{analysis_id}/data")
async def report_data(analysis_id: int, user: Dict[str, Any] = Depends(current_user)):
    """Return a stored analysis for the report page."""
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")
    analysis = await get_analysis(user["id"], analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

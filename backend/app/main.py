import logging
import uuid
import base64
import io
import csv
from datetime import datetime
from typing import List, Optional
from PIL import Image

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, UploadFile, File, HTTPException, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models import User, Inspection
from app.core.database import init_db, get_db
from app.core.auth import get_current_user, create_access_token, verify_password, hash_password
from app.schemas.inspection import InferenceResponse, ErrorResponse, AgentStatus
from app.services.agent_manager import agent_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("liveinspect-backend")

app = FastAPI(
    title="LiveInspectAI API",
    version="1.0.0",
    description="Production-grade Backend API & WebSocket Gateway for Real-time Visual Anomaly Detection"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()
    logger.info("Database schema initialized.")

# --- Schemas ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: Optional[str] = None

# --- System & Health Endpoints ---
@app.get("/healthz", tags=["System"])
async def healthz():
    return {"status": "ok", "app": "LiveInspectAI-API", "version": "1.0.0"}

@app.get("/readyz", tags=["System"])
async def readyz(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
        db_ready = True
    except Exception:
        db_ready = False

    return {
        "status": "ready" if db_ready else "degraded",
        "agent_online": agent_manager.is_connected(),
        "database": "ready" if db_ready else "error"
    }

@app.get("/api/v1/status", response_model=AgentStatus, tags=["Agent"])
async def get_agent_status():
    meta = agent_manager.agent_metadata
    return AgentStatus(
        agent_id=meta["agent_id"],
        online=agent_manager.is_connected(),
        status=meta["status"],
        last_seen=meta["last_seen"],
        model_name=meta["model_name"],
        category=meta["category"],
        hardware_device=meta["hardware_device"],
        queue_length=len(agent_manager.pending_inferences)
    )

# --- Authentication Endpoints ---
@app.post("/api/v1/auth/login", response_model=AuthTokenResponse, tags=["Auth"])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == req.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Email hoặc mật khẩu không đúng."}}
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name
    )

@app.get("/api/v1/auth/me", tags=["Auth"])
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }

# --- Agent Outbound WebSocket Endpoint ---
@app.websocket("/api/v1/agent/ws")
async def agent_websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    if token != settings.AGENT_TOKEN:
        logger.warning("Agent unauthorized connection attempt.")
        await websocket.close(code=4003, reason="Unauthorized")
        return

    await websocket.accept()
    await agent_manager.connect(websocket, settings.AGENT_ID)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "agent_hello":
                agent_manager.update_model_info(
                    model_name=data.get("model_name", "patchcore-screw"),
                    category=data.get("category", "screw"),
                    device=data.get("hardware_device", "NVIDIA GTX 1660 Ti")
                )
                await websocket.send_json({
                    "type": "hello_ack",
                    "status": "accepted",
                    "heartbeat_interval": settings.AGENT_HEARTBEAT_SECONDS
                })

            elif msg_type == "heartbeat":
                agent_manager.update_heartbeat()
                await websocket.send_json({"type": "heartbeat_ack"})

            elif msg_type == "infer_result":
                req_id = data.get("request_id")
                agent_manager.resolve_inference_result(req_id, data)

            elif msg_type == "infer_error":
                req_id = data.get("request_id")
                err_msg = data.get("error", "Inference error")
                agent_manager.reject_inference_result(req_id, err_msg)

    except WebSocketDisconnect:
        logger.info("Agent disconnected cleanly.")
        agent_manager.disconnect()
    except Exception as e:
        logger.error(f"WebSocket agent error: {e}")
        agent_manager.disconnect()

# --- Inference Endpoints ---
@app.post("/api/v1/inferences", response_model=InferenceResponse, tags=["Inference"])
async def run_inference(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_IMAGE_TYPE", "message": "Only JPEG, PNG, or WebP images are supported."}}
        )

    if not agent_manager.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": {"code": "AGENT_OFFLINE", "message": "Local AI Agent is currently offline."}}
        )

    file_bytes = await file.read()
    if len(file_bytes) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "IMAGE_TOO_LARGE", "message": "Image size exceeds limit (15MB)."}}
        )

    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        width, height = pil_img.size
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "CORRUPT_IMAGE", "message": "Failed to decode image data."}}
        )

    request_id = str(uuid.uuid4())
    img_b64 = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "type": "infer_request",
        "request_id": request_id,
        "category": "screw",
        "image_base64": img_b64,
        "width": width,
        "height": height
    }

    try:
        raw_result = await agent_manager.send_inference_request(payload, timeout_seconds=settings.INFERENCE_TIMEOUT_SECONDS)

        # Save to DB scoped by user
        record = Inspection(
            id=request_id,
            user_id=current_user.id,
            status="success",
            category="screw",
            model_name=raw_result.get("model_name", "patchcore-screw"),
            model_version=raw_result.get("model_version", "1.0.0"),
            prediction=raw_result.get("prediction", "NORMAL"),
            anomaly_score_raw=raw_result.get("anomaly_score_raw", 0.0),
            display_score=raw_result.get("display_score", 0.0),
            threshold=raw_result.get("threshold", 6.5),
            inference_ms=raw_result.get("inference_ms", 0.0),
            image_width=width,
            image_height=height,
            heatmap_png_base64=raw_result.get("heatmap_png_base64")
        )
        db.add(record)
        await db.commit()

        return InferenceResponse(
            request_id=request_id,
            status="success",
            model_name=record.model_name,
            model_version=record.model_version,
            category=record.category,
            prediction=record.prediction,
            anomaly_score_raw=record.anomaly_score_raw,
            display_score=record.display_score,
            threshold=record.threshold,
            inference_ms=record.inference_ms,
            image_width=width,
            image_height=height,
            heatmap_png_base64=record.heatmap_png_base64,
            created_at=record.created_at
        )

    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": {"code": "INFERENCE_TIMEOUT", "message": "Agent inference timed out."}}
        )
    except Exception as e:
        logger.error(f"Inference failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INFERENCE_FAILED", "message": str(e)}}
        )

# --- History & Inspection Records ---
@app.get("/api/v1/inspections", tags=["History"])
async def list_inspections(
    limit: int = 50,
    offset: int = 0,
    prediction: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Inspection).where(Inspection.user_id == current_user.id)
    if prediction:
        query = query.where(Inspection.prediction == prediction.upper())
    query = query.order_by(desc(Inspection.created_at)).offset(offset).limit(limit)

    res = await db.execute(query)
    items = res.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "created_at": i.created_at.isoformat(),
                "prediction": i.prediction,
                "anomaly_score_raw": i.anomaly_score_raw,
                "display_score": i.display_score,
                "threshold": i.threshold,
                "inference_ms": i.inference_ms,
                "image_width": i.image_width,
                "image_height": i.image_height,
                "heatmap_png_base64": i.heatmap_png_base64
            }
            for i in items
        ],
        "total": len(items)
    }

@app.get("/api/v1/inspections/export.csv", tags=["History"])
async def export_inspections_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Inspection)
        .where(Inspection.user_id == current_user.id)
        .order_by(desc(Inspection.created_at))
    )
    items = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp (UTC)", "Prediction", "Raw Score", "Display Score", "Threshold", "Latency (ms)", "Width", "Height"])
    for i in items:
        writer.writerow([i.id, i.created_at.isoformat(), i.prediction, i.anomaly_score_raw, i.display_score, i.threshold, i.inference_ms, i.image_width, i.image_height])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=liveinspect_history.csv"}
    )

@app.delete("/api/v1/inspections/{inspection_id}", tags=["History"])
async def delete_inspection(
    inspection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Inspection).where(Inspection.id == inspection_id, Inspection.user_id == current_user.id)
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inspection record not found")

    await db.delete(item)
    await db.commit()
    return {"status": "deleted", "id": inspection_id}

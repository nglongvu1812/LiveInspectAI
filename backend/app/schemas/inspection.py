from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class InferenceResponse(BaseModel):
    request_id: str
    status: Literal["success", "error"]
    model_name: str
    model_version: str
    category: str
    prediction: Literal["NORMAL", "ANOMALY", "UNCERTAIN"]
    anomaly_score_raw: float
    display_score: float
    threshold: float
    inference_ms: float
    image_width: int
    image_height: int
    heatmap_png_base64: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

class AgentStatus(BaseModel):
    agent_id: str
    online: bool
    status: str
    last_seen: Optional[datetime] = None
    model_name: Optional[str] = None
    category: Optional[str] = None
    hardware_device: Optional[str] = None
    queue_length: int = 0

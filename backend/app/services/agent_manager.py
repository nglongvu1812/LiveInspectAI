import logging
from typing import Dict, Optional, Any
from fastapi import WebSocket
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentConnectionManager:
    def __init__(self):
        self.active_agent_ws: Optional[WebSocket] = None
        self.agent_metadata: Dict[str, Any] = {
            "agent_id": "agent-win-gtx1660ti",
            "online": False,
            "status": "offline",
            "last_seen": None,
            "model_name": None,
            "category": "screw",
            "hardware_device": None,
        }
        self.pending_inferences: Dict[str, asyncio.Future] = {}
        self.inference_lock = asyncio.Lock()

    def is_connected(self) -> bool:
        return self.active_agent_ws is not None and self.agent_metadata["online"]

    async def connect(self, websocket: WebSocket, agent_id: str):
        self.active_agent_ws = websocket
        self.agent_metadata["agent_id"] = agent_id
        self.agent_metadata["online"] = True
        self.agent_metadata["status"] = "connected"
        self.agent_metadata["last_seen"] = datetime.utcnow()
        logger.info(f"Agent {agent_id} connected.")

    def disconnect(self):
        self.active_agent_ws = None
        self.agent_metadata["online"] = False
        self.agent_metadata["status"] = "offline"
        # Fail any pending futures
        for req_id, future in list(self.pending_inferences.items()):
            if not future.done():
                future.set_exception(RuntimeError("Agent disconnected during inference"))
        self.pending_inferences.clear()
        logger.warning("Agent disconnected. Cleared pending futures.")

    def update_heartbeat(self):
        self.agent_metadata["last_seen"] = datetime.utcnow()

    def update_model_info(self, model_name: str, category: str, device: str):
        self.agent_metadata["model_name"] = model_name
        self.agent_metadata["category"] = category
        self.agent_metadata["hardware_device"] = device
        self.agent_metadata["status"] = "ready"
        self.agent_metadata["last_seen"] = datetime.utcnow()

    async def send_inference_request(self, request_payload: dict, timeout_seconds: int = 30) -> dict:
        if not self.is_connected():
            raise ConnectionError("AGENT_OFFLINE")

        request_id = request_payload["request_id"]
        future = asyncio.get_event_loop().create_future()
        self.pending_inferences[request_id] = future

        try:
            async with self.inference_lock:
                await self.active_agent_ws.send_json(request_payload)
                result = await asyncio.wait_for(future, timeout=timeout_seconds)
                return result
        except asyncio.TimeoutError:
            raise TimeoutError("INFERENCE_TIMEOUT")
        finally:
            self.pending_inferences.pop(request_id, None)

    def resolve_inference_result(self, request_id: str, payload: dict):
        if request_id in self.pending_inferences:
            future = self.pending_inferences[request_id]
            if not future.done():
                future.set_result(payload)

    def reject_inference_result(self, request_id: str, error_msg: str):
        if request_id in self.pending_inferences:
            future = self.pending_inferences[request_id]
            if not future.done():
                future.set_exception(RuntimeError(error_msg))

agent_manager = AgentConnectionManager()

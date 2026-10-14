import argparse
import asyncio
import json
import logging
import os
import sys
import time
import base64
import io
from PIL import Image
import websockets
import torch

from inference import PatchCoreModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("liveinspect-agent")

class LiveInspectAgent:
    def __init__(self, server_url: str, token: str, model_path: str, device: str = "cuda"):
        self.server_url = server_url
        self.token = token
        self.model_path = model_path
        self.device = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        self.model = PatchCoreModel(device=self.device)
        self.running = True

    def load_model(self):
        logger.info(f"Loading PatchCore model from {self.model_path} onto {self.device}...")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model checkpoint not found at: {self.model_path}")
        self.model.load_checkpoint(self.model_path)
        logger.info("Model loaded successfully.")

    async def run(self):
        self.load_model()
        ws_url = f"{self.server_url}?token={self.token}"

        backoff = 2
        while self.running:
            try:
                logger.info(f"Connecting outbound to backend WebSocket at {self.server_url}...")
                async with websockets.connect(ws_url) as ws:
                    backoff = 2 # Reset backoff upon successful connection
                    logger.info("Connected to backend gateway.")

                    # 1. Send agent_hello
                    hello_msg = {
                        "type": "agent_hello",
                        "agent_id": "agent-win-gtx1660ti",
                        "model_name": "patchcore-screw",
                        "category": "screw",
                        "hardware_device": torch.cuda.get_device_name(0) if self.device == "cuda" else "CPU"
                    }
                    await ws.send(json.dumps(hello_msg))
                    logger.info("Sent agent_hello handshake.")

                    # 2. Main message processing loop
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
                    try:
                        async for raw_msg in ws:
                            data = json.loads(raw_msg)
                            msg_type = data.get("type")

                            if msg_type == "hello_ack":
                                logger.info("Received hello_ack from backend.")

                            elif msg_type == "infer_request":
                                await self._handle_infer_request(ws, data)

                            elif msg_type == "heartbeat_ack":
                                pass
                    finally:
                        heartbeat_task.cancel()

            except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError, OSError) as e:
                logger.warning(f"Connection lost ({e}). Reconnecting in {backoff} seconds...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
            except Exception as e:
                logger.error(f"Unexpected agent error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _heartbeat_loop(self, ws):
        try:
            while True:
                await asyncio.sleep(15)
                await ws.send(json.dumps({"type": "heartbeat"}))
        except asyncio.CancelledError:
            pass

    async def _handle_infer_request(self, ws, data: dict):
        req_id = data.get("request_id")
        img_b64 = data.get("image_base64")
        logger.info(f"Processing inference request: {req_id}")

        start_time = time.perf_counter()
        try:
            img_bytes = base64.b64decode(img_b64)
            pil_img = Image.open(io.BytesIO(img_bytes))

            pred = self.model.predict(pil_img)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            result_msg = {
                "type": "infer_result",
                "request_id": req_id,
                "model_name": "patchcore-screw",
                "model_version": "1.0.0",
                "category": "screw",
                "prediction": pred["prediction"],
                "anomaly_score_raw": pred["anomaly_score_raw"],
                "display_score": pred["display_score"],
                "threshold": pred["threshold"],
                "inference_ms": round(latency_ms, 2),
                "heatmap_png_base64": pred["heatmap_png_base64"]
            }
            await ws.send(json.dumps(result_msg))
            logger.info(f"Finished inference {req_id} in {latency_ms:.1f}ms: {pred['prediction']} (Score: {pred['anomaly_score_raw']})")

        except Exception as e:
            logger.error(f"Inference failure for {req_id}: {e}")
            await ws.send(json.dumps({
                "type": "infer_error",
                "request_id": req_id,
                "error": str(e)
            }))

def main():
    parser = argparse.ArgumentParser(description="LiveInspectAI Local Windows AI Agent")
    parser.add_argument("--server-url", type=str, default="ws://127.0.0.1:8000/api/v1/agent/ws")
    parser.add_argument("--token", type=str, default="liveinspect-secret-agent-token-xyz-123")
    parser.add_argument("--model-path", type=str, default="models/patchcore/screw_patchcore.pt")
    parser.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"])
    args = parser.parse_args()

    agent = LiveInspectAgent(
        server_url=args.server_url,
        token=args.token,
        model_path=args.model_path,
        device=args.device
    )
    asyncio.run(agent.run())

if __name__ == "__main__":
    main()

import asyncio
import io
import time
from PIL import Image
import httpx
import pytest
from app.main import app
from app.core.database import init_db
from app.services.agent_manager import agent_manager

@pytest.mark.asyncio
async def test_end_to_end_mock_agent_inference():
    await init_db()

    # Create dummy agent websocket runner
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Before agent connects -> 503
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(128, 128, 128)).save(buf, format="JPEG")
        files = {"file": ("screw_test.jpg", buf.getvalue(), "image/jpeg")}
        res = await ac.post("/api/v1/inferences", files=files)
        assert res.status_code == 503

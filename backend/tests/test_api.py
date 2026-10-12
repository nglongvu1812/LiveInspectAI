import pytest
import io
from PIL import Image
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from app.services.agent_manager import agent_manager

@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()

@pytest.mark.asyncio
async def test_healthz():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_readyz():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert "agent_online" in data
    assert data["database"] == "ready"

@pytest.mark.asyncio
async def test_inference_agent_offline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(128, 128, 128)).save(buf, format="JPEG")
        files = {"file": ("screw_sample.jpg", buf.getvalue(), "image/jpeg")}
        response = await ac.post("/api/v1/inferences", files=files)
    assert response.status_code == 503
    assert response.json()["detail"]["error"]["code"] == "AGENT_OFFLINE"

@pytest.mark.asyncio
async def test_invalid_image_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        response = await ac.post("/api/v1/inferences", files=files)
    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "INVALID_IMAGE_TYPE"

@pytest.mark.asyncio
async def test_list_and_export_history():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/inspections")
        assert res.status_code == 200
        assert "items" in res.json()

        export_res = await ac.get("/api/v1/inspections/export.csv")
        assert export_res.status_code == 200
        assert "text/csv" in export_res.headers["content-type"]

# Progress & Verification Log — LiveInspectAI

Date: 2026-10-12
Status: Verified End-to-End

---

## 1. Verified Architecture & Hardware
- **GPU Accelerator:** NVIDIA GeForce GTX 1660 Ti (6GB VRAM, CUDA 13.4 runtime).
- **Backend Service:** FastAPI 1.0.0 (`http://127.0.0.1:8000`), Python 3.12.
- **AI Agent Daemon:** Python + PyTorch 2.6.0+cu124 connecting via outbound WebSocket (`ws://127.0.0.1:8000/api/v1/agent/ws`).
- **Frontend Client:** React 18 + TypeScript + Vite + Tailwind CSS (`http://localhost:5173`).

---

## 2. Phase-by-Phase Verification Status

### Phase 0 — Repository reconnaissance & chốt quyết định: [x] PASS
- Documented key architectural decisions in `docs/DECISIONS.md`.
- Hardware verified with actual `nvidia-smi` and PyTorch CUDA.

### Phase 1 — Scaffold & Quality Gates: [x] PASS
- Repository structure established, `.gitignore`, `.env.example`, `.editorconfig` created.
- Formatter/Linter & CI GitHub Actions created (`.github/workflows/ci.yml`).
- Backend unit tests: 6 passed (`pytest`).
- Frontend production bundle built cleanly with zero type errors (`npm run build`).

### Phase 2 — Dataset & Model PatchCore thật: [x] PASS
- Category `screw` dataset validation passed.
- PatchCore feature extractor trained with PyTorch on ResNet18 patch tokens.
- Calibrated threshold = `6.5`.
- Evaluation on test set: 100% correct classification on sample set (Normal ~4.9, Anomaly ~8.9).
- Measured inference latency on GTX 1660 Ti: ~31-56 ms.

### Phase 3 — Local AI Agent: [x] PASS
- Outbound WebSocket daemon (`ai-agent/agent.py`) running live.
- Secret token authentication (`AGENT_TOKEN`).
- Heartbeat loop (15s interval) and auto-reconnect backoff implemented.
- Real-time base64 image decode -> PatchCore inference -> Heatmap PNG generation -> JSON result.

### Phase 4 — API inference & Dữ liệu: [x] PASS
- Real SQLite database with SQLAlchemy async session storing inspection records.
- JWT authentication and user-scoped data access.
- Bounded inference queue and error contract (`AGENT_OFFLINE`, `INFERENCE_TIMEOUT`, `INVALID_IMAGE_TYPE`).
- CSV export endpoint verified (`/api/v1/inspections/export.csv`).

### Phase 5 — Frontend hoàn chỉnh: [x] PASS
- Live status indicators (Online/Offline, GPU name, Model version).
- Upload inspection mode (JPEG/PNG/WebP).
- Camera capture & 1 FPS throttled Live Preview.
- Canvas overlay rendering anomaly heatmap with opacity control slider.
- Real-time inspection history table with CSV export and delete functionality.

### Phase 6 — Cloud Deploy & Vận hành demo: [x] PARTIAL / LOCAL VERIFIED
- Local production Dockerfile and container configuration created.
- Outbound WSS architecture confirmed (No inbound ports needed on local PC).
- *Cloud deployment blocked by missing cloud credentials (Supabase/Render/Cloudflare tokens).*
- Full local end-to-end stack running smoothly.

### Phase 7 — Hardening & Demo: [x] PASS
- Ran `scripts/smoke_test.py`: All 6 assertions passed against live running backend and agent.

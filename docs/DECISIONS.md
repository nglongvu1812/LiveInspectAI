# Architecture & Technical Decisions — LiveInspectAI

Date: 2026-10-12
Status: Approved

---

## 1. Context & Purpose
LiveInspectAI is an end-to-end student visual defect inspection system. The frontend and backend communicate with a local Windows PC running AI inference on an NVIDIA GeForce GTX 1660 Ti via an outbound Secure WebSocket (WSS).

---

## 2. Decision Log

### DEC-001: Machine Environment & Package Management
- **Hardware Verified:**
  - GPU: NVIDIA GeForce GTX 1660 Ti (6GB VRAM, Compute 7.5, Driver 617.42, CUDA 13.4 runtime compatible).
  - Python: 3.12.10 (System Python installed).
  - Node.js: v24.21.0, npm: 11.19.0.
  - Git: 2.56.0.windows.1.
- **Decision:**
  - Conda is not in system PATH; Python 3.12 standard virtual environments (`venv`) will be used for both Backend and AI-Agent/ML environments to ensure maximum reliability and portability on Windows 11 without requiring extra Anaconda installation steps.
  - PyTorch with CUDA 12.4/12.1 wheel support will be installed in the agent environment to leverage the GTX 1660 Ti GPU, with explicit CPU fallback supported.

### DEC-002: Repository Layout
- **Decision:**
  - Keep the existing directory structure inside `C:/Users/Admin/Documents/Project/LiveInspectAI` as planned in `PLAN.md`:
    - `backend/`: FastAPI backend service, schemas, WebSocket gateway, SQLite/PostgreSQL storage adapter.
    - `ai-agent/`: Local Python agent connecting outbound via WebSocket/WSS to backend, executing model inference.
    - `training/`: Dataset validator, training script, evaluation script, and model export.
    - `models/`: Model weights & artifacts (ignored in git).
    - `datasets/`: Local MVTec AD datasets (ignored in git).
    - `frontend/`: React + TypeScript + Vite web client.
    - `docs/`: Technical and operational documentation.
    - `scripts/`: Dev smoke test and utility scripts.

### DEC-003: Anomaly Detection Architecture (PatchCore)
- **Target Category:** MVTec AD `screw`.
- **Decision:**
  - Build a clean, self-contained, and reproducible PyTorch PatchCore implementation using a standard torchvision backbone (e.g. `wide_resnet50_2` or `resnet18` for fast GTX 1660 Ti inference with memory efficiency).
  - Preprocessing configuration: Target image size `224x224` (or `256x256` resized/cropped), ImageNet normalization (mean: `[0.485, 0.456, 0.406]`, std: `[0.229, 0.224, 0.225]`).
  - Output: Raw anomaly score (nearest neighbor distance in memory bank), calibrated percentile display score (0-100), prediction (`NORMAL`, `ANOMALY`, `UNCERTAIN`), inference latency in ms, and base64 PNG heatmap.

### DEC-004: Agent ↔ Backend Communication Protocol
- **Decision:**
  - Outbound persistent WebSocket connection from local AI Agent to backend `/api/v1/agent/ws`.
  - Authentication: Header `X-Agent-Token` or query param verified against backend `AGENT_TOKEN` secret.
  - Handshake: Agent sends `agent_hello` (agent_id, version, supported category, hardware device); Server replies `hello_ack`.
  - Inference Dispatch: Server sends `infer_request` with `request_id`, image base64, category.
  - Response: Agent sends `infer_result` (with matching `request_id`, prediction, score, heatmap_base64) or `infer_error`.
  - Heartbeat: Regular ping/pong or heartbeat messages to maintain connection and report status.
  - Concurrency: One active inference at a time on the agent, backend maintains a bounded queue (max 5 requests) and rejects new requests with `AGENT_BUSY` when full.

### DEC-005: Database & Authentication Strategy
- **Decision:**
  - Local Development Mode: SQLite database with SQLAlchemy/Aiosqlite and local JWT authentication to allow full zero-credential local end-to-end functionality without cloud blockers.
  - Cloud / Production Mode: Supabase PostgreSQL and Supabase Auth with RLS (Row Level Security).
  - Image Storage: Default `SAVE_IMAGES=false` (metadata only) to prevent privacy risks and cloud storage charges; support optional local disk / Supabase Storage private bucket when configured.

### DEC-006: Frontend Technology Stack
- **Decision:**
  - React 18 / 19 + TypeScript + Vite + Tailwind CSS + Lucide React.
  - Features:
    - Real-time webcam capture & single image upload.
    - Canvas overlay rendering real heatmap from model with opacity slider.
    - Throttled Live Preview (1 FPS max) with old frame dropping.
    - Inspection history with filtering, CSV export, and deletion.
    - Clear distinction between Agent Offline vs Inference Failure.

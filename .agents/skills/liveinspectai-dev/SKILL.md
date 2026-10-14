---
name: liveinspectai-dev
description: Development guidelines and rules for the LiveInspectAI project, including AI model development, FastAPI backend, local AI Agent, cloud communication, testing, and Git workflow.
---

# LiveInspectAI Development Skill

## Project context

LiveInspectAI is a student computer-vision project. The frontend and backend are deployed to the cloud, while AI inference runs on a local Windows PC with an NVIDIA GTX 1660 Ti.

## AI rules

- Start with one MVTec AD category, preferably screw.
- Separate training, evaluation, preprocessing, and inference code.
- Preserve the correct preprocessing configuration for each model.
- Return an anomaly score and anomaly map or mask.
- Do not claim general-purpose defect detection across arbitrary objects.
- Record model configuration and evaluation results.
- Do not invent benchmark metrics.

## Backend rules

- Use FastAPI with clear API schemas and service boundaries.
- Keep model inference separate from HTTP and WebSocket handlers.
- Validate uploaded image types, dimensions, and payload sizes.
- Handle inference failures and disconnected AI Agents.
- Use environment variables for secrets.

## AI Agent and cloud rules

- Authenticate the local AI Agent.
- Prefer secure outbound WSS connections from the local PC.
- Do not expose the local inference service directly to the public Internet.
- Handle reconnects, timeouts, stale frames, and unavailable agents.
- Never report a successful inference if the model failed.

## Testing rules

- Add tests for preprocessing, inference output shape, API validation, and session management.
- Run relevant tests before marking an issue complete.
- Report actual test results and known limitations.
- Use real measurements for latency and model evaluation.

## Git workflow

- Implement one GitHub issue at a time.
- Inspect existing files before modifying them.
- Avoid unrelated refactoring.
- Update documentation when behavior or setup changes.
- Never commit secrets, large datasets, or unnecessary model files.

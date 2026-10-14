# LiveInspectAI — Agent Instructions

## Project goal
Build a computer vision anomaly detection application using PatchCore and Anomalib, with a React frontend, FastAPI backend, and a local AI agent running on a Windows PC with an NVIDIA GTX 1660 Ti.

## Architecture
- Frontend: React, TypeScript, Vite.
- Backend: Python, FastAPI.
- AI inference: local Windows PC.
- Initial dataset: MVTec AD, starting with one category such as `screw`.
- Communication: authenticated WebSocket over TLS for cloud connections.
- Database: PostgreSQL.
- Deployment: cloud frontend and backend; inference remains on the local PC.

## Development rules
1. Read `README.md` and the existing project structure before changing files.
2. Implement one GitHub issue at a time.
3. Do not rewrite unrelated modules without approval.
4. Keep AI inference independent from HTTP and WebSocket handlers.
5. Use environment variables for secrets and deployment settings.
6. Never commit API keys, passwords, tokens, or private datasets.
7. Add tests for important functionality.
8. Run relevant tests and report their actual results.
9. Do not claim a feature is complete if it has not been tested.
10. Document setup steps and dependency versions.
11. Do not assume every object category can be detected reliably by a single model.
12. Avoid unnecessary dependencies and paid services.

## Workflow
Before implementing an issue:
- Summarize the intended changes.
- Identify affected files and dependencies.
- Identify the acceptance criteria.

After implementation:
- List changed files.
- Report commands executed and test results.
- List known limitations and remaining tasks.
- Update documentation when setup or behavior changes.

## Priority
1. Local inference on a static image.
2. FastAPI image inference endpoint.
3. Local AI agent communication.
4. Camera UI and anomaly mask overlay.
5. Cloud deployment.
6. Evaluation, testing, documentation, and final demo.
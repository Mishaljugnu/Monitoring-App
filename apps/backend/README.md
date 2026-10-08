# NetVision AI Backend

FastAPI service responsible for telemetry collection, network/process inspection, AI analysis, reports, and the WebSocket telemetry stream.

Run from the repository root:

```bash
python -m uvicorn app.main:app --app-dir apps/backend --host 127.0.0.1 --port 8000
```

Health check: `GET /health`

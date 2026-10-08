# NetVision AI Run Guide

This guide explains how to install, configure, run, and troubleshoot the NetVision AI desktop network monitoring application.

## 1. Project Location

```powershell
D:\UNI\college\s4\mr luqman\uas project\application
```

Open a terminal in that folder before running the commands below.

## 2. Technology Stack

- Backend: FastAPI, Python, SQLAlchemy, SQLite, WebSockets
- Frontend: React, TypeScript, Vite, Tailwind CSS, Zustand, Recharts
- Desktop shell: Electron
- AI providers: Ollama, OpenAI, Gemini, Claude
- Local database: `netvision_ai.db`

## 3. Prerequisites

Install these first:

1. Node.js and npm
2. Python 3.10 or newer
3. Git, optional but recommended
4. Ollama, optional for local AI chat
5. Npcap, optional for better packet/process bandwidth capture on Windows

The app still runs without Ollama or Npcap, but AI chat may use fallback responses and per-process bandwidth may be limited.

## 4. Install Dependencies

From the project root:

```powershell
npm install
npm install -w apps/desktop
pip install -r apps/backend/requirements.txt
```

If dependencies are already installed, you can skip this step.

## 5. Configure Environment Variables

The backend reads settings from environment variables with the `NETVISION_` prefix.

Optional setup:

```powershell
Copy-Item apps/backend/env.example apps/backend/.env
```

Then edit:

```text
apps/backend/.env
```

Important values:

```env
NETVISION_DEFAULT_AI_PROVIDER=ollama
NETVISION_OLLAMA_BASE_URL=http://127.0.0.1:11434
NETVISION_OLLAMA_MODEL=llama3.2
```

For cloud AI providers, fill only the provider you plan to use:

```env
NETVISION_OPENAI_API_KEY=
NETVISION_GEMINI_API_KEY=
NETVISION_ANTHROPIC_API_KEY=
```

## 6. Configure Ollama

If you want local AI chat:

```powershell
ollama serve
ollama pull llama3.2
```

Check installed models:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags | ConvertTo-Json -Depth 5
```

The configured model must match an installed Ollama model. The app is currently configured for:

```text
llama3.2
```

## 7. Run the Full Application

From the project root:

```powershell
npm run dev
```

This starts:

1. FastAPI backend at `http://127.0.0.1:8000`
2. Vite frontend at `http://127.0.0.1:5173`
3. Electron desktop window

Open the browser version here:

```text
http://127.0.0.1:5173/
```

## 8. Run Backend Only

Use this when debugging API or telemetry:

```powershell
python -m uvicorn app.main:app --app-dir apps/backend --host 127.0.0.1 --port 8000 --reload
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected result:

```json
{"status":"ok"}
```

## 9. Run Frontend Only

Use this only if the backend is already running:

```powershell
npm run dev -w apps/desktop
```

Frontend URL:

```text
http://127.0.0.1:5173/
```

## 10. Build for Production

```powershell
npm run build
```

This runs TypeScript checks and builds the Vite frontend.

## 11. Useful API Endpoints

Backend base URL:

```text
http://127.0.0.1:8000
```

Common endpoints:

```text
GET  /health
GET  /api/v1/bootstrap
GET  /api/v1/history
GET  /api/v1/alerts
GET  /api/v1/devices
GET  /api/v1/processes
GET  /api/v1/connections
GET  /api/v1/ai/analysis
GET  /api/v1/ai/providers
POST /api/v1/ai/chat
GET  /api/v1/reports/summary
GET  /api/v1/reports/export?format=json
GET  /api/v1/reports/export?format=csv
WS   /ws/telemetry
```

## 12. Test AI Chat from PowerShell

```powershell
Invoke-RestMethod `
  http://127.0.0.1:8000/api/v1/ai/chat `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"message":"WHAT IS MY IP","provider":"ollama"}'
```

## 13. Export Reports

JSON report:

```powershell
Invoke-WebRequest `
  'http://127.0.0.1:8000/api/v1/reports/export?format=json' `
  -OutFile netvision-report.json
```

CSV telemetry export:

```powershell
curl.exe -o netvision-telemetry.csv `
  'http://127.0.0.1:8000/api/v1/reports/export?format=csv'
```

## 14. Troubleshooting

### Backend port is already in use

Check what is using port `8000`:

```powershell
netstat -ano | findstr :8000
```

Stop the process if needed:

```powershell
taskkill /PID <PID> /F
```

### Frontend port is already in use

Check port `5173`:

```powershell
netstat -ano | findstr :5173
```

Then stop the process if needed.

### Ollama says model not found

Install the configured model:

```powershell
ollama pull llama3.2
```

Or change:

```env
NETVISION_OLLAMA_MODEL=<installed-model-name>
```

### AI provider appears offline

Open the Settings tab and refresh provider status. For Ollama, make sure:

1. Ollama is running.
2. The model is installed.
3. `NETVISION_OLLAMA_MODEL` matches the installed model.

### Warning: No libpcap provider available

This usually means packet capture support is missing. Install Npcap on Windows if you want better packet/process bandwidth capture.

The app can still run without it.

### Electron closes and stops the dev stack

The current dev script uses `concurrently -k`, so closing Electron can stop the frontend/backend processes. Run `npm run dev` again from the project root.

### WebSocket disconnected

Make sure the backend is running at:

```text
http://127.0.0.1:8000
```

Then refresh the frontend page.

## 15. Recommended Startup Checklist

1. Open PowerShell.
2. Go to the project root:

```powershell
cd "D:\UNI\college\s4\mr luqman\uas project\application"
```

3. Start Ollama, optional:

```powershell
ollama serve
```

4. Run the app:

```powershell
npm run dev
```

5. Open:

```text
http://127.0.0.1:5173/
```

6. Confirm backend health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 16. Notes

- The app uses real local telemetry.
- AI recommendations are generated from collected metrics.
- Cloud AI providers require API keys.
- SQLite data is stored in `netvision_ai.db`.
- The app is currently intended for local desktop use, not public network deployment.


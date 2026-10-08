# NetVision AI

A desktop network monitoring and diagnostics application that combines live system telemetry, network/process inspection, historical metrics, alerts, reports, and AI-assisted analysis.

## What it demonstrates

- **Desktop product engineering:** Electron + React + TypeScript
- **Backend engineering:** FastAPI + SQLAlchemy + SQLite
- **Live telemetry:** CPU, memory, network and host-level monitoring
- **Network visibility:** devices, connections and process/network activity
- **Real-time updates:** WebSocket telemetry stream
- **AI-assisted diagnostics:** provider abstraction for OpenAI, Gemini, Claude and Ollama, with a deterministic fallback
- **Reporting:** JSON/CSV export and historical telemetry storage
- **Research/product documentation:** included research paper

## Architecture

```text
Electron
  └── React + TypeScript UI
        │ HTTP / WebSocket
        ▼
FastAPI backend
  ├── Runtime monitor
  ├── Network/process services
  ├── AI analysis + chat
  ├── Alerting
  ├── Predictive analytics
  └── Report generation
        │
        ▼
SQLite telemetry store
```

## Repository layout

```text
netvision-ai/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   ├── requirements.txt
│   │   └── env.example
│   └── desktop/
│       ├── electron/
│       ├── src/
│       └── package.json
├── scripts/
├── NetVision_AI_Research_Paper.docx
├── LICENSE
└── README.md
```

## Run locally

### 1. Install backend dependencies

```bash
python -m venv .venv
```

Activate the environment, then:

```bash
pip install -r apps/backend/requirements.txt
```

### 2. Install frontend dependencies

```bash
npm install
npm install --prefix apps/desktop
```

### 3. Configure AI providers (optional)

Copy `apps/backend/env.example` to `apps/backend/.env` and add credentials only for providers you want to use. The application can fall back to a deterministic data-grounded assistant when no external provider is configured.

### 4. Start the desktop application

```bash
npm run dev
```

The Electron development launcher starts the Vite frontend and automatically starts the FastAPI backend. To use a different Python executable, set `NETVISION_PYTHON` before running the command.

If you prefer to start the backend manually:

```bash
python -m uvicorn app.main:app --app-dir apps/backend --host 127.0.0.1 --port 8000
```

Then run the desktop frontend separately with:

```bash
npm run dev -w apps/desktop
```

## Build the frontend

```bash
npm run build -w apps/desktop
```

This creates the production web assets used by Electron. Packaging a fully self-contained desktop installer still requires bundling a Python runtime and the backend dependencies; this repository intentionally keeps that deployment step separate.

## API configuration

The desktop client defaults to `http://127.0.0.1:8000`. You can override it for development with:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The WebSocket endpoint is derived automatically from the same base URL.

## Important platform notes

NetVision reads telemetry from the machine where its backend runs. That means the real monitoring product is a **desktop/local application**, not a conventional server-hosted web dashboard.

It is therefore not intended to be deployed as a normal Vercel/Netlify application. A hosted portfolio demo would need a separate fixture/demo-data mode that does not expose or collect the visitor's machine telemetry.

Some network inspection features may require elevated permissions or behave differently across Windows, macOS and Linux.

## Security notes

- Do not commit `.env` files or API keys.
- The backend binds to localhost by default.
- AI providers receive only the information sent through their configured integration.
- Review permissions before enabling low-level network inspection on a production machine.

## Research

`NetVision_AI_Research_Paper.docx` contains the associated research/documentation artifact.

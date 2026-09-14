# FaceTrack — Command Reference

Every command you need to set up, run, test and deploy the project. Paths are
relative to the repository root unless noted.

```
FaceTrack/
├── backend/     # FastAPI + OpenCV + YOLOv8 + dlib
├── frontend/    # Next.js 14 + TypeScript + Tailwind
└── database/    # SQLite database file (auto-created)
```

---

## 1. Prerequisites

| Tool    | Version | Notes |
|---------|---------|-------|
| Python  | 3.10 – 3.12 | 3.11 recommended for `dlib` wheels |
| Node.js | ≥ 18.18 | 20 LTS recommended |
| CMake   | latest  | Required to build `dlib` (face recognition) |
| Git     | latest  | |

```bash
# macOS
brew install python@3.11 node cmake

# Ubuntu / Debian
sudo apt update && sudo apt install -y python3.11 python3.11-venv nodejs npm cmake build-essential libgl1 libglib2.0-0

# Windows (PowerShell, via winget)
winget install Python.Python.3.11 OpenJS.NodeJS.LTS Kitware.CMake
```

---

## 2. Backend (FastAPI)

### 2.1 One-line launch (creates venv + installs + runs)

```bash
# macOS / Linux
cd backend && ./run.sh

# Windows (PowerShell)
cd backend; .\run.ps1
```

### 2.2 Manual setup

```bash
cd backend

# Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate           # Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# (optional) configure environment
cp .env.example .env                # then edit SECRET_KEY etc.

# Run the API (auto-reload for development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API base:            http://localhost:8000
- Interactive docs:    http://localhost:8000/docs
- OpenAPI schema:      http://localhost:8000/openapi.json
- Health check:        http://localhost:8000/api/v1/health

> On first start the database tables are created and a default admin user
> (`admin` / `admin123`) is provisioned automatically.

### 2.3 If `face_recognition` / `dlib` fails to install

The app **still runs** without it (person detection works; face matching is
disabled and reported via `/api/v1/model-status`). To install it:

```bash
pip install cmake
pip install dlib
pip install face-recognition
```

### 2.4 Tests & quality

```bash
cd backend
source .venv/bin/activate
python -m pytest -q                 # run the test suite
python -m compileall app            # byte-compile / syntax check
```

---

## 3. Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Configure the API URL (defaults to http://localhost:8000)
cp .env.local.example .env.local    # edit if the backend is elsewhere

# Development server (http://localhost:3000)
npm run dev

# Production build + start
npm run build
npm run start

# Lint
npm run lint
```

Open http://localhost:3000 and sign in with `admin` / `admin123`.

---

## 4. Full stack — quick start (two terminals)

```bash
# Terminal 1 — backend
cd backend && ./run.sh

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

---

## 5. Docker

```bash
# Build & run the backend image
cd backend
docker build -t facetrack-backend .
docker run -p 8000:8000 facetrack-backend

# Or the whole stack from the repo root
docker compose up --build
```

---

## 6. Common API calls (cURL)

```bash
# Login → capture token
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Dashboard stats
curl -s localhost:8000/api/v1/attendance/stats -H "Authorization: Bearer $TOKEN"

# Model / engine status
curl -s localhost:8000/api/v1/model-status

# Start live recognition on the local webcam (device 0)
curl -s -X POST localhost:8000/api/v1/recognition/start \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"source_type":"webcam","source":"0","camera_name":"Webcam"}'

# View the annotated MJPEG feed in a browser
open http://localhost:8000/api/v1/recognition/feed   # macOS

# Stop recognition
curl -s -X POST localhost:8000/api/v1/recognition/stop -H "Authorization: Bearer $TOKEN"

# Export attendance CSV
curl -s "localhost:8000/api/v1/reports/export?start_date=2026-01-01&end_date=2026-12-31" \
  -H "Authorization: Bearer $TOKEN" -o attendance.csv
```

---

## 7. Reset / maintenance

```bash
# Wipe the database (a fresh one is recreated on next start)
rm -f database/attendance.db

# Clear stored face photos & snapshots
rm -f backend/storage/faces/* backend/storage/snapshots/*

# Remove Python venv / Node modules
rm -rf backend/.venv frontend/node_modules frontend/.next
```

---

## 8. Environment variables

### Backend (`backend/.env`)
| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me...` | JWT signing key — **set in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime |
| `FIRST_ADMIN_USERNAME` / `FIRST_ADMIN_PASSWORD` | `admin` / `admin123` | Bootstrap admin |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `DATABASE_URL` | `sqlite:///.../attendance.db` | Any SQLAlchemy URL |
| `YOLO_CONFIDENCE` | `0.4` | Person-detection threshold |
| `FACE_RECOGNITION_THRESHOLD` | `0.45` | Minimum match confidence |
| `FACE_MATCH_TOLERANCE` | `0.55` | Max face distance for a match |
| `FRAME_SKIP` | `2` | Process every Nth frame |
| `ATTENDANCE_COOLDOWN_SECONDS` | `60` | Re-mark cooldown per person |
| `WORKDAY_START` | `09:15` | Arrivals after this are "late" |

### Frontend (`frontend/.env.local`)
| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |
| `NEXT_PUBLIC_API_PREFIX` | `/api/v1` | API prefix |

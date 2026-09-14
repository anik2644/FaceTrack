<div align="center">

# 🎯 FaceTrack

### Real-time CCTV-based Person Detection & Face-Recognition Attendance Platform

*Detect people in a live camera feed with **YOLOv8**, recognise faces with **dlib**,
and log attendance automatically — all through a modern **FastAPI + Next.js** stack.*

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-3-06B6D4?logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 📖 Overview

FaceTrack turns any webcam or IP/RTSP CCTV camera into an automated attendance
system. A **YOLOv8** detector locates people in the frame, each person region is
passed to a **dlib** face encoder, and the resulting 128-d embedding is matched
against an enrolled gallery. Recognised individuals are marked present (or late)
in real time, streamed to a live dashboard, and made available for reporting and
CSV export.

The codebase is built as a clean, layered application — **SOLID principles**,
the **Repository** and **Service** patterns, **Strategy** for pluggable
detectors, a **Facade** recognition pipeline and a **Singleton** stream manager —
so it reads well, tests easily and extends without friction.

---

## ✨ Features

### Recognition & Vision
- 🧍 **Person detection** with YOLOv8 (COCO class *person*).
- 🙂 **Face recognition** with dlib 128-d embeddings and nearest-neighbour matching.
- 🎞️ **Low-latency streaming** — dedicated capture thread + single-slot buffer + frame-skipping.
- 🗂️ **Multi-sample enrollment** — several encodings per person for robustness across angles/lighting.
- 📺 **Annotated MJPEG feed** with bounding boxes, names, confidence and an FPS HUD.
- 🔌 **Graceful degradation** — the server still runs if YOLO or dlib are unavailable, and reports engine status.

### Attendance
- ⏱️ **Automatic marking** with a configurable per-person cooldown (no spam).
- 🌅 **Late detection** against a configurable workday start time.
- 📅 **Daily / ranged queries**, per-department filtering.
- 📊 **Dashboard** with live stats, 7-day trend and today's check-ins.

### Management & Reporting
- 👥 **Person CRUD** — enroll via webcam or file upload, add extra face samples, activate/deactivate.
- 🎥 **Camera management** — save webcam/RTSP/HTTP sources with connectivity testing.
- 📈 **Reports & analytics** — per-person summaries, stacked daily-trend charts.
- 📥 **CSV export** for any date range.

### Platform
- 🔐 **JWT authentication** with bcrypt password hashing and a bootstrap admin.
- 🔴 **WebSocket** live detection feed (with polling fallback).
- 🧱 **Clean, modular architecture** and typed API contracts end-to-end.
- 📚 **Auto-generated OpenAPI docs** at `/docs`.
- 🐳 **Docker** support.

---

## 🏛️ Architecture

```
┌──────────────────────────┐         HTTP / WS          ┌───────────────────────────────┐
│        Next.js UI        │  ───────────────────────▶  │            FastAPI            │
│  App Router · TS · TW    │  ◀───────────────────────  │       (API v1 routers)        │
└──────────────────────────┘   JSON · MJPEG · events    └───────────────┬───────────────┘
                                                                         │
                          ┌──────────────────────────────────────────────┼───────────────────────┐
                          │                          Services (business logic)                     │
                          │  Auth · Person · Attendance · Report · Camera · Vision pipeline        │
                          └───────────────┬───────────────────────────────┬───────────────────────┘
                                          │ Repositories (data access)     │ Vision (Strategy/Facade)
                                          ▼                                 ▼
                                 ┌─────────────────┐             ┌──────────────────────────┐
                                 │  SQLite (ORM)   │             │ YOLOv8 · dlib · OpenCV   │
                                 └─────────────────┘             └──────────────────────────┘
```

### Backend layout (`backend/app`)
```
app/
├── main.py                 # App factory, lifespan, middleware, static mounts
├── core/                   # config · logging · security (JWT/bcrypt) · exceptions
├── db/                     # SQLAlchemy base · session · init/bootstrap
├── models/                 # ORM: User · Person · FaceEncoding · Attendance · Camera
├── schemas/                # Pydantic request/response contracts
├── repositories/           # Repository pattern — isolates persistence
├── services/               # Business logic (one service per domain)
│   └── vision/             # detector · encoder · gallery · matcher · pipeline · stream · manager
├── api/
│   ├── deps.py             # DI: session, current user, service providers
│   ├── websocket.py        # WS connection manager (thread-safe broadcast)
│   └── v1/                 # routers: auth · persons · attendance · reports · cameras · recognition · system
└── utils/                  # image (base64/JPEG) helpers
```

### Frontend layout (`frontend/src`)
```
src/
├── app/
│   ├── login/                    # Auth screen
│   └── (dashboard)/              # Protected shell (sidebar + topbar)
│       ├── page.tsx              # Dashboard (stats + charts)
│       ├── monitor/              # Live recognition (MJPEG + WS events)
│       ├── persons/              # Person management
│       ├── register/             # Enrollment (webcam/upload)
│       ├── attendance/           # Attendance records
│       ├── reports/              # Analytics + CSV export
│       ├── cameras/              # Camera management
│       └── settings/             # Account + engine status
├── components/                   # Sidebar · Topbar · StatCard · WebcamCapture · ui/*
├── lib/                          # api client · auth context · utils
└── types/                        # Shared TS types mirroring the API
```

---

## 🧰 Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Recharts, Axios, lucide-react |
| **Backend** | FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0, python-jose (JWT), bcrypt |
| **Vision / ML** | Ultralytics YOLOv8, face_recognition (dlib), OpenCV, NumPy |
| **Database** | SQLite (any SQLAlchemy-supported DB via `DATABASE_URL`) |
| **Tooling** | pytest, Docker, ESLint |

---

## 🚀 Quick Start

> Full command reference: **[commands.md](./commands.md)**

**1. Backend**
```bash
cd backend
./run.sh                     # macOS/Linux  (Windows: .\run.ps1)
# API → http://localhost:8000   ·   Docs → http://localhost:8000/docs
```

**2. Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                  # UI → http://localhost:3000
```

**3. Sign in** with the default credentials:

```
username: admin
password: admin123
```

---

## 🔑 Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Obtain a JWT |
| `GET`  | `/api/v1/auth/me` | Current user |
| `GET/POST` | `/api/v1/persons` | List / enroll persons |
| `POST` | `/api/v1/persons/{id}/encodings` | Add a face sample |
| `POST` | `/api/v1/recognition/start` | Start live recognition |
| `GET`  | `/api/v1/recognition/feed` | Annotated MJPEG stream |
| `WS`   | `/api/v1/recognition/ws` | Live detection events |
| `GET`  | `/api/v1/attendance/stats` | Dashboard statistics |
| `GET`  | `/api/v1/attendance` | Query attendance by range |
| `GET`  | `/api/v1/reports/summary` | Per-person summary |
| `GET`  | `/api/v1/reports/export` | CSV export |
| `GET/POST` | `/api/v1/cameras` | Manage cameras |
| `GET`  | `/api/v1/model-status` | ML engine status |

Explore them all interactively at **http://localhost:8000/docs**.

---

## ⚙️ Configuration

Both apps are configured via environment files — see the tables in
**[commands.md](./commands.md#8-environment-variables)**. Copy the examples and
edit as needed:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

> **Production checklist:** set a strong `SECRET_KEY`, change the default admin
> password, and restrict `BACKEND_CORS_ORIGINS`.

---

## 🧪 Testing

```bash
cd backend && source .venv/bin/activate && python -m pytest -q   # backend
cd frontend && npm run build                                      # frontend typecheck + build
```

---

## 🧠 How Recognition Works

1. **Capture** — a background thread reads frames into a single-slot buffer (freshest frame only → low latency).
2. **Detect** — YOLOv8 finds person bounding boxes (`FRAME_SKIP` controls how often).
3. **Encode** — each person crop is downscaled and passed to dlib to produce 128-d face embeddings.
4. **Match** — embeddings are compared to the in-memory gallery via Euclidean distance; a match must pass both a distance tolerance and a confidence threshold.
5. **Mark** — recognised people are recorded (respecting the cooldown), flagged present/late, broadcast over WebSocket and drawn on the annotated feed.

---

## 🗺️ Roadmap Ideas

- Liveness / anti-spoofing detection
- Multi-camera simultaneous streams
- Role-based access control (viewer / operator / admin)
- Email / webhook alerts on unknown faces
- PostgreSQL + Alembic migrations for production

---

## 📄 License

Released under the **MIT License** — see [`LICENSE`](./LICENSE).

## 🙏 Acknowledgments

[Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) ·
[dlib / face_recognition](https://github.com/ageitgey/face_recognition) ·
[OpenCV](https://opencv.org/) ·
[FastAPI](https://fastapi.tiangolo.com/) ·
[Next.js](https://nextjs.org/)

<div align="center"><sub>Built with ❤️ for real-time computer vision.</sub></div>

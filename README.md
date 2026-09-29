# 🅿️ AI-Powered Smart Curb & Parking Intelligence Platform
### Smart India Hackathon (SIH) — Smart Mobility & Urban Traffic Optimization

An enterprise-grade, end-to-end computer vision and IoT analytics platform that transforms municipal CCTV infrastructure into real-time curb management, parking availability tracking, and automated parking violation enforcement. Built with a high-contrast **Black & White Minimalist UI/UX** and strict role-based CCTV security.

---

## 🌟 Key Capabilities

- **Real-Time Parking Space Monitoring**: Computes exact slot occupancy using polygon-intersection IoU geometry with sub-second latency.
- **Strict CCTV Camera Privacy & Access Control**:
  - 👮 **Parking Enforcement Officers**: Exclusive access to live CCTV camera streams, surveillance footage, and violation monitoring.
  - 👤 **Citizens & Unauthorized Users**: CCTV camera lists, streams, and raw footage are **strictly blocked** to protect citizen privacy and municipal security.
- **Automated Violation Detection**: Detects unauthorized curbside parking in:
  - 🚫 No Parking Zones
  - 🔴 Blocked Fire Hydrants
  - 🚨 Emergency Access / Ambulance Lanes
  - 🚌 Designated Bus Stops
- **Temporal & Role-Based Rules**: Configurable duration thresholds per zone type (e.g. 10s for hydrants vs 30s for general curb) preventing false positives from transient stops.
- **Vehicle Classification**: Distinguishes between Private Passenger Cars, Commercial Delivery Vehicles, and Emergency Vehicles.
- **Automated Evidence Capture**: Generates annotated JPEG snapshots featuring vehicle bounding boxes, zone outlines, timestamps, and confidence metrics.
- **Officer Verification & Footage Player**: Enforcement officers can inspect photographic evidence, view live CCTV video streams, confirm violations, or reject invalid alerts.
- **Live WebSocket Telemetry**: Dual-channel live feeds for real-time occupancy updates and high-priority violation push alerts.
- **High-Performance Parking Discovery**: Searchable, filterable curb zone cards with real-time slot layout (P-01, P-02, P-03...) and capacity counters (no map dependency).
- **Strict Role-Based Access Control (RBAC)**:
  - 👤 **Citizen Driver**: View vacant parking spots, search curb zones, manage profile.
  - 👮 **Traffic Officer**: Real-time violation alerts, live CCTV camera feeds & footage, evidence review & adjudication.
  - 🛡️ **System Administrator**: Full platform control, user management, advanced analytics, audit logs.

---

## 🏗️ System Architecture

```text
 ┌────────────────────────────────────────────────────────┐
 │            Municipal CCTV / RTSP / Video Feeds         │
 └──────────────────────────┬─────────────────────────────┘
                            │ Frame Stream
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │                    AI Ingestion Engine                 │
 │  • YOLOv8 Vehicle Detection (Car, Bus, Truck, Moto)    │
 │  • ByteTrack Multi-Object Real-Time Tracking           │
 │  • Shapely Polygonal IoU Overlap Evaluator             │
 │  • Temporal Rule Engine (Duration & Zone Logic)        │
 │  • Annotated Evidence Snapshot Generator               │
 └──────────────────────────┬─────────────────────────────┘
                            │ HTTP POST (Internal X-AI-Key)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │                 FastAPI Backend Service                │
 │  • RESTful API (Auth, Parking, Violations, Analytics)  │
 │  • CCTV Streaming (/api/v1/cameras/{id}/footage)       │
 │  • WebSockets (/ws/occupancy & /ws/violations)         │
 │  • SlowAPI Rate Limiting & Argon2 Password Hashing     │
 │  • SQLAlchemy Async ORM (SQLite Dev / PostgreSQL Prod) │
 └──────────────────────────┬─────────────────────────────┘
                            │ REST + WebSocket (JWT Guard)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │        React 19 + TypeScript Monochrome UI/UX          │
 │  • High-Contrast Black & White Swiss Minimalist Design │
 │  • Officer-Only CCTV Footage Player Modal              │
 │  • Live WebSocket Dashboards & Alert Banners           │
 │  • Evidence Image Review & Modal Adjudication          │
 │  • Chart.js Monochrome Analytics                       │
 └────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **AI / CV Pipeline** | Python 3.11, Ultralytics YOLOv8, OpenCV, ByteTrack, Shapely, Structlog |
| **Backend API** | FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2, SlowAPI, HTTPX, Pytest |
| **Database** | SQLite + AioSQLite (Development) / PostgreSQL 15 + PostGIS (Production) |
| **Frontend** | React 19, TypeScript, Vite, React Router v7, Chart.js, Lucide Icons |
| **Design System** | Minimalist Black & White Monochrome (Deep Carbon `#000000`, High-Contrast Whites `#ffffff`) |
| **Security** | Argon2id Hashing, JWT (HS256), Role Guards (Citizen / Officer / Admin) |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher
- **Git**

### 2. Automated 1-Click Launch (Windows)
Double-click `run_all.bat` from the project root:
```bat
run_all.bat
```
This automatically boots:
1. FastAPI Backend on `http://localhost:8000`
2. React Web Dashboard on `http://localhost:5173`
3. AI Processing Pipeline streaming `data/videos/curb_surveillance.mp4`

---

### 3. Step-by-Step Manual Launch

#### Step 3.1: Seed the Database
```powershell
.\seed_db.bat
```
*Creates database tables and seeds demo users, cameras, zones, and parking slots.*

#### Step 3.2: Start the Backend
```powershell
.\run_backend.bat
```
*API available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.*

#### Step 3.3: Start the Frontend
```powershell
.\run_frontend.bat
```
*Dashboard available at `http://localhost:5173`.*

#### Step 3.4: Start the AI Pipeline
```powershell
.\run_ai.bat
```
*Begins object detection, tracking, occupancy evaluation, and violation alerting.*

---

## 🔑 Demo Credentials

The login screen features **1-click quick-fill buttons** for instant switching between roles:

| Role | Email | Password | Permissions & Visibility |
|---|---|---|---|
| **Traffic Officer** | `officer@smartparking.com` | `Officer@1234` | **Exclusive CCTV Feeds**, live violation alerts, evidence verification, camera streams |
| **Citizen Driver** | `citizen@smartparking.com` | `Citizen@1234` | Parking search, live slot availability, settings (**CCTV cameras blocked**) |
| **System Admin** | `admin@smartparking.com` | `Admin@1234` | Full platform control, user management, full analytics, CCTV footage |

---

## 🧪 Automated Testing & Verification

The platform includes **57 automated unit and integration tests** with **100% pass rate**:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v --tb=short
```

### Test Suite Breakdown:
- **`test_api.py`** (35 tests):
  - Health checks & system status
  - Authentication (Login, Argon2 verification, public signup, duplicate checks)
  - Full RBAC matrix (Public vs Citizen vs Officer vs Admin access)
  - **CCTV Camera Footage Security**: Officer allowed, Citizen blocked (403), Unauthenticated blocked (401/403)
  - Parking zones & Haversine distance geocoding search
  - Violation adjudication workflow (Pending -> Confirmed / Rejected)
  - Live AI ingestion security (X-AI-Key header validation)
  - Occupancy & Violation Analytics endpoints
  - User profile & admin user management
- **`test_full_system.py`** (5 tests):
  - AI Pipeline rules & parking slot occupancy calculation
  - Evidence frame generation & bounding box drawing
  - Password hashing & JWT token expiration
- **`test_phase1_config.py`** (17 tests):
  - Configuration loading, environment variables, camera schemas, zone polygons

### Frontend Build Verification:
```powershell
cd frontend
npm run build
```
*Compiles all pages, TypeScript types, and Vite bundles with 0 errors in under 1 second.*

---

## 📡 API Reference Summary

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Service health & version status |
| `POST` | `/api/v1/auth/login` | Public | Authenticate user & return JWT token |
| `POST` | `/api/v1/auth/signup` | Public | Citizen self-registration |
| `POST` | `/api/v1/auth/register` | Admin | Register new officer or admin account |
| `GET` | `/api/v1/parking/` | Public | List all parking zones & occupancy |
| `GET` | `/api/v1/parking/nearby` | Public | Haversine radius search for nearest spots |
| `GET` | `/api/v1/cameras/` | **Officer, Admin ONLY** | List all active CCTV camera feeds |
| `GET` | `/api/v1/cameras/{id}/footage`| **Officer, Admin ONLY** | Stream municipal CCTV video footage |
| `GET` | `/api/v1/violations/` | **Officer, Admin ONLY** | List violations with status & camera filter |
| `PATCH`| `/api/v1/violations/{id}/status` | **Officer, Admin ONLY** | Confirm or reject a pending violation |
| `GET` | `/api/v1/violations/{id}/evidence`| **Officer, Admin ONLY** | Retrieve annotated evidence JPEG image |
| `POST` | `/api/v1/live/occupancy` | Internal (AI Key)| Ingest real-time slot occupancy data |
| `POST` | `/api/v1/live/violation` | Internal (AI Key)| Ingest real-time violation event |
| `WS`   | `/api/v1/live/ws/occupancy` | Public | WebSocket stream of live parking availability |
| `WS`   | `/api/v1/live/ws/violations`| **Officer, Admin ONLY** | Authenticated WebSocket stream of violation alerts |
| `GET` | `/api/v1/analytics/violations`| **Officer, Admin ONLY** | Violation counts & category breakdown |
| `GET` | `/api/v1/analytics/occupancy` | Admin | Historical average and peak occupancy rates |

---

## 💡 SISTEC Innovation Hackathon Demo Presentation Flow

1. **Demonstrate CCTV Privacy Isolation**:
   - Log in as **Citizen** (`citizen@smartparking.com`).
   - Notice the navigation contains only **Overview**, **Parking Zones**, and **Settings**.
   - Attempting to visit `/cameras` displays the **Access Restricted Security Gate**.
2. **Log In as Traffic Officer**:
   - Use the 1-click **"👮 Officer"** quick-fill button on the login screen.
   - The navigation now unlocks **Live Stream**, **Violations**, **CCTV Cameras**, and **Analytics**.
3. **Watch Real-Time CCTV Camera Footage**:
   - Navigate to **CCTV Cameras (`/cameras`)**.
   - Click **"▶ Watch CCTV Stream"** on `CAM-001`.
   - A surveillance player HUD opens with live video playback, resolution, frame rate, and YOLOv8 detection overlay.
4. **Inspect & Adjudicate Violations (`/violations`)**:
   - Filter by `Pending Review`.
   - Click **"🖼️ Evidence"** on a violation to view the annotated photograph with vehicle bounding boxes, violation duration, and confidence metrics.
   - Click **"✓ Confirm Violation"** or **"✗ Reject"**.
5. **Real-Time Telemetry (`/live`)**:
   - Inspect dual streaming indicators (`Occupancy Socket` and `Violation Alerts`).
6. **Curbside Parking Discovery (`/parking`)**:
   - Experience the new black & white spot locator with real-time slot grids (`P-01`, `P-02`...) and instant search.

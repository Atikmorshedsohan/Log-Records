# Computer Log Collector

A lightweight, scalable log collection pipeline using **FastAPI**, **Fluent Bit**, and **Supabase (PostgreSQL)** to collect system logs (Windows Event Log, Linux Systemd, HTTP, etc.) and store them in Supabase for querying and visualization.

---

## 🏗️ Architecture

```
[ Windows Event Log / Linux Journal / HTTP Logs ]
                        │
                        ▼
               [ Fluent Bit Agent ]
           (Collects, buffers, filters)
                        │  HTTP POST
                        ▼
              [ FastAPI Backend ]
           (Ingests & normalizes logs)
                        │
                        ▼
             [ Supabase Database ]
         (Table: `public.computer_events`)
```

---

## 🚀 Quick Start

### 1. Database Setup (Supabase)
Run the SQL migration in [supabase_schema.sql](supabase_schema.sql) in your **Supabase SQL Editor**:
- Creates table `public.computer_events` with appropriate indexes.
- Configures Row Level Security (RLS) policies for ingestion and querying.

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your Supabase credentials:
   ```bash
   cp .env.example .env
   ```
5. Start the backend:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 3. Log Ingestion (Fluent Bit)
- **Linux / Docker**:
  ```bash
  docker compose up -d
  ```
- **Windows**:
  Run Fluent Bit using [fluent-bit/windows.conf](fluent-bit/windows.conf):
  ```powershell
  fluent-bit -c fluent-bit/windows.conf
  ```

---

## 📡 API Endpoints

- `GET /`: Health status and Supabase connection state.
- `GET /health`: Basic liveness probe.
- `POST /ingest` or `POST /api/logs`: Ingestion endpoint supporting both standard JSON and Newline-Delimited JSON (`json_lines`).

---

## 🔒 Security

- Sensitive credentials (`.env`) are excluded from version control via `.gitignore`.
- Provide your own Supabase project URL and API key in `backend/.env`.

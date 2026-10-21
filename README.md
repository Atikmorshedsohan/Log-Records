# Windows Log Collector (Fluent Bit + FastAPI + Supabase)

A lightweight, high-performance system log collection pipeline designed for Windows. It collects native **Windows Event Logs** (`System`, `Application`, and `Security`) using a direct **Fluent Bit** agent, forwards them to a **FastAPI** backend for validation and parsing, and stores them in **Supabase (PostgreSQL)** for real-time querying and visualization.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│                  Windows Host                │
│                                              │
│   Windows Event Log (System, Application)    │
│                       │                      │
│                       ▼                      │
│     Direct Native Fluent Bit Service/Agent   │
│       (C:\Program Files\fluent-bit)          │
│                       │                      │
│                       ▼ HTTP POST (NDJSON)   │
│             FastAPI Backend API              │
│            (http://127.0.0.1:8000)           │
└───────────────────────┬──────────────────────┘
                        │
                        ▼ Supabase Client (HTTPS)
             ┌─────────────────────┐
             │  Supabase Database  │
             │  (computer_events)  │
             └─────────────────────┘
```

### 💡 Why Native Fluent Bit (No Docker)?
Windows Event Logs utilize the native Windows Event Logging API (`wevtapi.dll`). Running Fluent Bit inside Linux Docker containers cannot access host Windows kernel and system events. Running Fluent Bit natively directly on Windows ensures seamless, low-latency collection without virtualization overhead.

---

## 📁 Project Structure

```
Log collector/
├── backend/
│   ├── main.py              # FastAPI application (endpoints: /ingest, /api/logs, /)
│   ├── requirements.txt     # Python dependencies (FastAPI, Supabase, Uvicorn, etc.)
│   ├── test_api.py          # Automated test suite for endpoints
│   ├── .env.example         # Template for environment variables
│   └── .env                 # (Ignored) Secret Supabase keys & host config
├── fluent-bit/
│   ├── windows.conf         # Direct Windows Fluent Bit config (winlog plugin)
│   └── fluent-bit.yaml      # YAML alternative config
├── supabase_schema.sql      # Database schema, table definitions, and RLS policies
├── .gitignore               # Excludes secrets, venv, databases, and logs
└── README.md                # Documentation
```

---

## 🚀 Quick Setup & Usage

### 1. Database Setup (Supabase)
1. Go to your **[Supabase Dashboard](https://supabase.com/dashboard)**.
2. Open the **SQL Editor**.
3. Copy and run the queries inside [`supabase_schema.sql`](supabase_schema.sql):
   - Creates the `public.computer_events` table.
   - Configures indexes for fast queries by hostname and timestamp.
   - Applies Row Level Security (RLS) policies allowing insert and select operations.

---

### 2. Backend Setup (FastAPI)

1. Open a PowerShell terminal in the project root:
   ```powershell
   cd "c:\Users\KINGDOM\Desktop\Log collector"
   ```

2. Activate the virtual environment (or create one):
   ```powershell
   .\.venv\Scripts\activate
   # If installing fresh:
   # pip install -r backend/requirements.txt
   ```

3. Configure your environment:
   Ensure `backend/.env` contains your Supabase credentials:
   ```ini
   HOST=0.0.0.0
   PORT=8000
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_or_service_role_key
   ```

4. Start the backend:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. Verify the backend is running:
   Open `http://127.0.0.1:8000/` in your browser. It should return:
   ```json
   {
     "service": "Computer Log Collector Backend",
     "status": "healthy",
     "supabase_connected": true
   }
   ```

---

### 3. Run Native Fluent Bit (Direct Ingestion)

1. Ensure Fluent Bit for Windows is installed (default location: `C:\Program Files\fluent-bit`).
2. In a separate PowerShell terminal (run as **Administrator** if collecting the `Security` channel), execute:
   ```powershell
   & "C:\Program Files\fluent-bit\bin\fluent-bit.exe" -c "fluent-bit\windows.conf"
   ```

Fluent Bit will immediately begin streaming Windows Event Logs to your backend, which inserts them into Supabase.

---

## ⚙️ Fluent Bit Configuration Details (`windows.conf`)

- **`[INPUT] (winlog)`**:
  - `Channels System,Application`: Collects system and application events. (Add `Security` when running with Administrator privileges).
  - `Interval_Sec 1`: Polls for new events every second.
  - `DB winlog.db`: Tracks offset in a local SQLite file so duplicate events are never re-sent across restarts.
- **`[FILTER] (record_modifier)`**:
  - Attaches standard tags (`os_type: windows`, `hostname`).
- **`[OUTPUT] (http)`**:
  - Forwards records via HTTP POST to `http://127.0.0.1:8000/ingest` using efficient `json_lines` format.

---

## 📊 Viewing Ingested Logs

You can view the logs stored in Supabase:
1. Open your Supabase Dashboard $\rightarrow$ **Table Editor** $\rightarrow$ select **`computer_events`**.
2. Or query via the **SQL Editor**:
   ```sql
   SELECT id, hostname, event_category, event_level, source, message, received_at
   FROM public.computer_events
   ORDER BY received_at DESC
   LIMIT 50;
   ```

---

## 🔒 Security Best Practices

- All secrets (`.env`) are excluded from Git via `.gitignore`.
- Only use `.env.example` as a template.
- Optional: Configure `COLLECTOR_TOKEN` in `backend/.env` and `windows.conf` if you want token-based request authorization on the `/ingest` endpoint.

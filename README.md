# Cross-Platform Log Collector (Fluent Bit + FastAPI + Supabase)

A lightweight, high-performance system log collection pipeline designed for **Windows** and **Linux** without requiring Docker.

- **On Windows**: Collects native Windows Event Logs (`System`, `Application`, and `Security`) via the `winlog` plugin.
- **On Linux**: Collects native Systemd Journal logs (kernel, services, authentication, syslog) via the `systemd` plugin.
- **Backend**: FastAPI normalizes and validates events across OS types and writes them in real time into **Supabase (PostgreSQL)**.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│       Host System (Windows or Linux)         │
│                                              │
│   Windows Event Log  OR  Systemd Journal     │
│                       │                      │
│                       ▼                      │
│        Direct Native Fluent Bit Agent        │
│    (windows.conf         linux.conf)         │
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

---

## 📁 Project Structure

```
Log collector/
├── backend/
│   ├── main.py              # FastAPI application (multi-OS normalization & ingestion)
│   ├── requirements.txt     # Python dependencies (FastAPI, Supabase, Uvicorn, etc.)
│   ├── test_api.py          # Automated test suite for endpoints
│   ├── .env.example         # Template for environment variables
│   └── .env                 # (Ignored) Secret Supabase keys & host config
├── fluent-bit/
│   ├── windows.conf         # Direct Windows Fluent Bit config (winlog plugin)
│   ├── linux.conf           # Direct Linux Fluent Bit config (systemd plugin)
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

Runs on either Windows or Linux:

```bash
# Clone and enter directory
cd "Log collector"

# Create and activate virtual environment
# Windows:
python -m venv .venv
.\.venv\Scripts\activate

# Linux:
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

Configure `backend/.env` with your Supabase credentials:
```ini
HOST=0.0.0.0
PORT=8000
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_role_key
```

Start the backend:
```bash
# Windows
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Linux
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health at `http://127.0.0.1:8000/` (`"supabase_connected": true`).

---

### 3. Run Fluent Bit Directly (No Docker)

#### Option A: On Windows
1. Install Fluent Bit from the official website (installs to `C:\Program Files\fluent-bit`).
2. Run in PowerShell (as **Administrator** if collecting the `Security` channel):
   ```powershell
   & "C:\Program Files\fluent-bit\bin\fluent-bit.exe" -c "fluent-bit\windows.conf"
   ```

#### Option B: On Linux (Ubuntu / Debian / CentOS / RHEL)
1. Install Fluent Bit directly on your Linux host:
   ```bash
   # Ubuntu / Debian official one-line install
   curl https://raw.githubusercontent.com/fluent/fluent-bit/master/install.sh | sh
   ```
2. Run Fluent Bit directly using `linux.conf`:
   ```bash
   fluent-bit -c fluent-bit/linux.conf
   ```
3. *(Optional)* Run as a persistent background service on Linux:
   ```bash
   sudo systemctl enable fluent-bit
   sudo systemctl start fluent-bit
   ```

---

## ⚙️ Configuration Comparison

| Feature | Windows (`windows.conf`) | Linux (`linux.conf`) |
| :--- | :--- | :--- |
| **Plugin** | `winlog` | `systemd` |
| **Log Source** | Event Log (`System`, `Application`) | Systemd Journal (`/run/log/journal`) |
| **Offset DB** | `winlog.db` (local SQLite) | `/var/log/fluent-bit-systemd.db` |
| **OS Tag** | `os_type windows` | `os_type linux` |
| **Target Output** | `http://127.0.0.1:8000/ingest` | `http://127.0.0.1:8000/ingest` |

---

## 📊 Viewing Ingested Logs

Open your **[Supabase Table Editor](https://supabase.com/dashboard)** under `public.computer_events`, or run in SQL Editor:

```sql
SELECT id, hostname, os_type, event_category, event_level, source, message, received_at
FROM public.computer_events
ORDER BY received_at DESC
LIMIT 50;
```

---

## 🔒 Security Best Practices

- All sensitive keys (`.env`) are strictly ignored via `.gitignore`.
- If sending logs from a remote Linux/Windows machine to your central FastAPI server, replace `127.0.0.1` in the config output with your server's IP address.

import datetime
import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from supabase import create_client, Client

from pathlib import Path

# Load environment variables (check both backend folder and current working directory)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

app = FastAPI(
    title="Computer Log Collector API",
    description="Backend API for collecting and storing system logs into Supabase",
    version="1.0.0",
)

# Supabase Client Initialization
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "your_supabase_project_url":
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")


@app.get("/")
def read_root():
    return {
        "service": "Computer Log Collector Backend",
        "status": "healthy",
        "supabase_connected": supabase is not None,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ingest")
@app.post("/api/logs")
async def collect_logs(
    request: Request,
    x_collector_token: str | None = Header(default=None, alias="X-Collector-Token"),
):
    """
    Endpoint to receive logs from Fluent Bit (supports both standard JSON and json_lines / NDJSON).
    """
    # Verify optional collector token if configured in .env
    expected_token = os.getenv("COLLECTOR_TOKEN")
    if expected_token and x_collector_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid X-Collector-Token")

    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8", errors="ignore").strip()

    raw_items: list = []
    if body_text:
        try:
            # Check if payload is standard JSON or JSON array
            parsed = json.loads(body_text)
            raw_items = parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            # Parse Format json_lines (Newline Delimited JSON)
            for line in body_text.splitlines():
                line = line.strip()
                if line:
                    try:
                        raw_items.append(json.loads(line))
                    except Exception:
                        raw_items.append({"raw": line})

    if not raw_items:
        raw_items = [{"raw": body_text}]

    # Helper function to map raw log dictionary to computer_events schema
    def map_to_computer_event(item: dict) -> dict:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        hostname = item.get("hostname") or item.get("Computer") or item.get("host") or "unknown-host"
        os_type = item.get("os_type") or "windows"
        event_time = item.get("event_time") or item.get("TimeCreated") or item.get("TimeGenerated") or item.get("timestamp") or now_iso
        event_category = item.get("event_category") or item.get("Channel") or item.get("channel")
        event_level = item.get("event_level") or item.get("Level") or item.get("level")
        source = item.get("source") or item.get("ProviderName") or item.get("SourceName")
        message = item.get("message") or item.get("Message") or item.get("Description")

        return {
            "hostname": str(hostname),
            "os_type": str(os_type),
            "event_time": event_time,
            "received_at": now_iso,
            "event_category": str(event_category) if event_category else None,
            "event_level": str(event_level) if event_level else None,
            "source": str(source) if source else None,
            "message": str(message) if message else None,
            "event_data": item if isinstance(item, dict) else {"raw": str(item)},
        }

    # Forward to Supabase 'computer_events' table if configured
    if supabase is not None:
        mapped_records = [
            map_to_computer_event(item) if isinstance(item, dict) else map_to_computer_event({"raw": item})
            for item in raw_items
        ]
        try:
            response = supabase.table("computer_events").insert(mapped_records).execute()
            return {"status": "success", "inserted": len(mapped_records), "data": response.data}
        except Exception as err:
            raise HTTPException(
                status_code=500,
                detail=f"Database insertion error into 'computer_events': {str(err)}",
            )

    return {
        "status": "received",
        "message": "Log received (Supabase not connected, please configure .env)",
        "count": len(raw_items),
        "payload": raw_items,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)


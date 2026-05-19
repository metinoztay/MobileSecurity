import asyncio
import json
import uuid
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import os
import shutil

from backend.workflows.scanner_graph import create_scanner_graph
from backend.core.state import ScannerState
from backend.core.config import config

app = FastAPI(title="Mobile Security Agent API")

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active scans (in a real app, use Redis/DB)
active_scans = {}
scanner_app = create_scanner_graph()

@app.post("/api/scan")
async def start_scan(file: UploadFile = File(None), use_mock: str = Form("true")):
    """
    Tarama baslatir ve scan_id dondurur.
    Eger file yuklenmisse onu kaydeder.
    """
    scan_id = str(uuid.uuid4())
    
    is_mock = use_mock.lower() == "true"
    
    apk_path = "/mock/path/app.apk"
    source_code = {}
    
    if is_mock or not file:
        apk_path = "/mock/path/app.apk"
        source_code = {
            "MainActivity.java": "public class MainActivity { public static final String API_KEY = 'AKIAIOSFODNN7EXAMPLE'; }",
            "NetworkConfig.xml": "<network-security-config><base-config cleartextTrafficPermitted='true'/></network-security-config>"
        }
    else:
        # Gerçek dosya yüklendi
        os.makedirs(config.WORKSPACE_DIR, exist_ok=True)
        apk_path = os.path.join(config.WORKSPACE_DIR, f"{scan_id}.apk")
        with open(apk_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Decompile Agent'ın çalışması için source_code boş bırakılır
        source_code = {}
    
    # Mock Initial State
    initial_state = ScannerState(
        scan_id=scan_id,
        apk_path=apk_path,
        source_code=source_code,
        network_traffic=[
            {
                "url": "http://api.example.com/login",
                "method": "POST",
                "headers": {"Authorization": "Basic YWRtaW46YWRtaW4="},
                "body": '{"username": "admin", "password": "password123"}'
            }
        ],
        findings=[],
        current_phase="init",
        next_agent="",
        completed_agents=[],
        final_report="",
        errors=[]
    )
    
    active_scans[scan_id] = {
        "state": initial_state,
        "status": "running"
    }
    
    return {"scan_id": scan_id, "message": "Scan started", "apk_path": apk_path, "is_mock": is_mock}

@app.get("/api/stream/{scan_id}")
async def stream_scan(scan_id: str, request: Request):
    """
    SSE uzerinden LangGraph ciktisini frontend'e akitir.
    """
    if scan_id not in active_scans:
        return {"error": "Scan not found"}
        
    async def event_generator():
        initial_state = active_scans[scan_id]["state"]
        config = {"recursion_limit": 100}
        
        try:
            # yield first message
            yield json.dumps({"type": "info", "message": "Tarama başlatılıyor..."})
            await asyncio.sleep(0.5)
            
            # Use LangGraph's astream to get async events
            async for output in scanner_app.astream(initial_state, config=config):
                # If client disconnects
                if await request.is_disconnected():
                    break
                    
                for key, value in output.items():
                    event_data = {
                        "type": "agent_update",
                        "agent": key,
                        "details": {}
                    }
                    
                    if key == "orchestrator":
                        event_data["details"]["message"] = f"Orkestratör düşünüyor... Sıradaki ajan: {value.get('next_agent')}"
                    elif key == "decompile_agent":
                        event_data["details"]["message"] = "Sistem: APK dosyası decompile ediliyor..."
                        event_data["details"]["source_code"] = value.get("source_code")
                    elif key == "hardcoded_secrets_agent":
                        event_data["details"]["message"] = "Statik Analiz: Hardcoded Secret aranıyor..."
                    elif key == "insecure_comm_agent":
                        event_data["details"]["message"] = "Dinamik Analiz: Ağ trafiği inceleniyor..."
                    elif key == "owasp_mapper_agent":
                        event_data["details"]["message"] = "Raporlama: OWASP Top 10 eşleştirmesi yapılıyor..."
                        event_data["details"]["final_report"] = value.get("final_report")
                        event_data["details"]["raw_findings"] = value.get("findings", [])
                        
                    yield json.dumps(event_data)
                    await asyncio.sleep(1.5) # Arayuzde animasyonun gorunmesi icin ufak gecikme
                    
            yield json.dumps({"type": "done", "message": "Tarama tamamlandı."})
            
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)})
            
    return EventSourceResponse(event_generator())

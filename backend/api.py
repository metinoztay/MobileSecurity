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
            "AndroidManifest.xml": "<?xml version='1.0' encoding='utf-8'?><manifest xmlns:android='http://schemas.android.com/apk/res/android' package='com.example.vulnerable'>\n  <uses-permission android:name='android.permission.READ_EXTERNAL_STORAGE'/>\n  <uses-permission android:name='android.permission.WRITE_EXTERNAL_STORAGE'/>\n  <uses-permission android:name='android.permission.INTERNET'/>\n  <application android:allowBackup='true' android:debuggable='true' android:usesCleartextTraffic='true'>\n    <activity android:name='.MainActivity' android:exported='true'>\n      <intent-filter>\n        <action android:name='android.intent.action.VIEW'/>\n        <category android:name='android.intent.category.DEFAULT'/>\n        <category android:name='android.intent.category.BROWSABLE'/>\n        <data android:scheme='vulnerableapp' android:host='login'/>\n      </intent-filter>\n    </activity>\n    <receiver android:name='.MyBroadcastReceiver' android:exported='true'>\n      <intent-filter><action android:name='com.example.UPDATE_DATA'/></intent-filter>\n    </receiver>\n    <provider android:name='.MyContentProvider' android:authorities='com.example.provider' android:exported='true' android:grantUriPermissions='true'/>\n    <service android:name='.MyService' android:exported='true'/>\n  </application>\n</manifest>",
            "MainActivity.java": "package com.example.vulnerable;\nimport android.webkit.WebView;\nimport android.util.Log;\nimport android.content.SharedPreferences;\nimport android.content.Intent;\nimport android.net.Uri;\nimport android.os.Bundle;\nimport android.app.Activity;\nimport java.security.MessageDigest;\nimport javax.crypto.Cipher;\nimport javax.crypto.spec.SecretKeySpec;\nimport java.io.File;\nimport java.io.FileOutputStream;\n\npublic class MainActivity extends Activity {\n    // Hardcoded Secrets\n    public static final String AWS_SECRET_KEY = \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\";\n    public static final String DB_PASS = \"supersecret123\";\n    \n    protected void onCreate(Bundle savedInstanceState) {\n        super.onCreate(savedInstanceState);\n        \n        // Insecure Storage (SharedPreferences & External File)\n        SharedPreferences prefs = getSharedPreferences(\"user_prefs\", MODE_PRIVATE);\n        prefs.edit().putString(\"session_token\", \"token_12345\").apply();\n        try {\n            File extFile = new File(getExternalFilesDir(null), \"backup.txt\");\n            FileOutputStream fos = new FileOutputStream(extFile);\n            fos.write(DB_PASS.getBytes());\n        } catch(Exception e) {}\n        \n        // Webview Security\n        WebView webView = new WebView(this);\n        webView.getSettings().setJavaScriptEnabled(true);\n        webView.getSettings().setAllowFileAccessFromFileURLs(true);\n        webView.addJavascriptInterface(new Object(), \"Android\");\n        \n        // Crypto (Weak MD5 & AES ECB)\n        try {\n            MessageDigest md = MessageDigest.getInstance(\"MD5\");\n            byte[] key = \"hardcodedkey1234\".getBytes();\n            SecretKeySpec secretKeySpec = new SecretKeySpec(key, \"AES\");\n            Cipher cipher = Cipher.getInstance(\"AES/ECB/PKCS5Padding\");\n            cipher.init(Cipher.ENCRYPT_MODE, secretKeySpec);\n        } catch(Exception e) {}\n        \n        // Data Leakage\n        Log.d(\"SensitiveInfo\", \"User Password logged: \" + DB_PASS);\n        \n        // Intent Spoofing (Implicit Broadcast)\n        Intent intent = new Intent(\"com.example.INTERNAL_ACTION\");\n        intent.putExtra(\"secret_data\", \"confidential_info\");\n        sendBroadcast(intent);\n        \n        // Deep link Analyzer (Open arbitrary URL without validation)\n        Uri data = getIntent().getData();\n        if(data != null) { webView.loadUrl(data.getQueryParameter(\"url\")); }\n    }\n}",
            "DatabaseHelper.java": "package com.example.vulnerable;\nimport android.database.sqlite.SQLiteDatabase;\n\npublic class DatabaseHelper {\n    public void getUserInfo(SQLiteDatabase db, String username) {\n        // SQL Injection (String concatenation)\n        String query = \"SELECT * FROM users WHERE username = '\" + username + \"'\";\n        db.rawQuery(query, null);\n    }\n}",
            "NetworkConfig.xml": "<network-security-config>\n  <base-config cleartextTrafficPermitted='true'>\n    <trust-anchors>\n      <certificates src='system'/>\n      <certificates src='user'/>\n    </trust-anchors>\n  </base-config>\n</network-security-config>",
            "MyContentProvider.java": "package com.example.vulnerable;\nimport android.content.ContentProvider;\n// Insecure Content Provider\npublic class MyContentProvider extends ContentProvider {\n    @Override\n    public boolean onCreate() { return true; }\n    // query, insert, update, delete omitted for brevity but exported=true allows unrestricted access\n}"
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
                "body": '{"username": "admin", "password": "password123"}',
                "response_status": 200,
                "response_body": '{"token": "eyJhbGciOiJIUzI1NiIsInR5cCI... (No HttpOnly flag)"}'
            },
            {
                "url": "https://api.example.com/transfer",
                "method": "POST",
                "headers": {"Cookie": "session_id=12345"},
                "body": '{"amount": 1000, "to": "attacker"}',
                "response_status": 200,
                "response_body": '{"status": "success", "txid": "9999"}'
            },
            {
                "url": "http://api.example.com/profile?name=<script>alert(1)</script>",
                "method": "GET",
                "headers": {},
                "body": "",
                "response_status": 200,
                "response_body": '<html><body>Welcome <script>alert(1)</script></body></html>'
            },
            {
                "url": "https://api.example.com/admin_panel",
                "method": "GET",
                "headers": {"Role": "Guest"},
                "body": "",
                "response_status": 200,
                "response_body": '{"admin_data": "Top secret company financials"}'
            },
            {
                "url": "https://api.example.com/users?id=1' OR '1'='1",
                "method": "GET",
                "headers": {},
                "body": "",
                "response_status": 200,
                "response_body": '[{"id":1,"name":"admin"},{"id":2,"name":"user"}]'
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

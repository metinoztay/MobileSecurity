import os
import subprocess
import urllib.request
import shutil
from backend.core.state import ScannerState
from backend.core.config import config

def decompile_agent(state: ScannerState) -> dict:
    """
    APK dosyasını apktool kullanarak decompile eder ve gerekli dosyaları source_code state'ine ekler.
    LLM kullanmaz, sistem aracı olarak çalışır.
    """
    apk_path = state.get("apk_path", "")
    scan_id = state.get("scan_id", "default_scan")
    current_source_code = state.get("source_code", {})
    
    # Eğer zaten decompile edildiyse veya apk değilse atla
    if not apk_path.endswith(".apk") or current_source_code:
        return {"current_phase": "decompile_done"}

    workspace = config.WORKSPACE_DIR
    apktool_path = os.path.join(workspace, "apktool.jar")
    out_dir = os.path.join(workspace, f"decompiled_{scan_id}")
    
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
    
    # 1. Apktool.jar yoksa indir
    if not os.path.exists(apktool_path):
        print("[Decompile Agent] apktool.jar indiriliyor...")
        apktool_url = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
        try:
            urllib.request.urlretrieve(apktool_url, apktool_path)
        except Exception as e:
            print(f"[Decompile Agent] Apktool indirme hatası: {e}")
            return {"current_phase": "decompile_error", "errors": state.get("errors", []) + [str(e)]}

    # 2. Decompile işlemini başlat
    print(f"[Decompile Agent] {apk_path} decompile ediliyor...")
    try:
        # java -jar apktool.jar d apk_path -o out_dir -f
        subprocess.run(
            ["java", "-jar", apktool_path, "d", apk_path, "-o", out_dir, "-f"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore')
        print(f"[Decompile Agent] Apktool çalıştırma hatası: {error_msg}")
        return {"current_phase": "decompile_error", "errors": state.get("errors", []) + [error_msg]}

    # 3. Kritik dosyaları oku
    source_code = {}
    
    # Okunacak hedef dosyalar (Göreceli yollar)
    target_files = [
        "AndroidManifest.xml",
        "res/values/strings.xml",
        "res/xml/network_security_config.xml"
    ]
    
    for relative_path in target_files:
        full_path = os.path.join(out_dir, relative_path.replace("/", os.sep))
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # Çok uzunsa kes (LLM token sınırını korumak için)
                    if len(content) > 15000:
                        content = content[:15000] + "\n...[TRUNCATED]"
                    source_code[relative_path] = content
            except Exception as e:
                print(f"[Decompile Agent] {relative_path} okunamadı: {e}")
    
    return {
        "source_code": source_code,
        "current_phase": "decompile_done"
    }

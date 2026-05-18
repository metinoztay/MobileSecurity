from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

def insecure_storage_agent(state: ScannerState) -> dict:
    """
    static agent: insecure_storage_agent
    """
    llm = get_llm()
    source_code = state.get("source_code", {})
    if not source_code:
        return {"current_phase": "static_done"}
        
    system_prompt = """Sen bir Mobil Depolama Güvenlik Uzmanısın.
Görevin kaynak kodda SharedPreferences, SQLite veritabanı veya harici depolamada (External Storage) hassas verilerin düz metin (plaintext) olarak saklanıp saklanmadığını incelemektir.
    
Bulgularını aşağıdaki JSON formatında bir liste olarak döndürmelisin:
    [
      {
        "vulnerability_name": "...",
        "severity": "High/Medium/Low",
        "description": "Detaylı açıklama",
        "affected_files": ["dosya_yolu"],
        "remediation": "Çözüm önerisi"
      }
    ]
    Eğer zafiyet yoksa boş liste `[]` döndür. Sadece JSON döndür.
    """
    
    context_text = ""
    for path, content in source_code.items():
        context_text += f"\n--- DOSYA: {path} ---\n{content[:2000]}\n"
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"İşte incelemen gereken veri:\n{context_text}")
    ])
    
    new_findings = []
    report_update = ""
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        parsed = json.loads(content)
        
        if isinstance(parsed, list):
            new_findings = parsed
            for f in new_findings:
                if isinstance(f, dict):
                    f["source_agent"] = "insecure_storage_agent" 
        elif isinstance(parsed, dict) and "report_update" in parsed:
            report_update = parsed["report_update"]
        elif isinstance(parsed, dict) and "mapped_findings" in parsed: # OWASP special
            report_update = json.dumps(parsed, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"[insecure_storage_agent] JSON parse hatası: {e}")

    result_state = {"current_phase": "static_done"}
    if new_findings:
        current_findings = state.get("findings", [])
        current_findings.extend(new_findings)
        result_state["findings"] = current_findings
        
    if report_update:
        current_report = state.get("final_report", "")
        current_report += f"\n\n=== INSECURE_STORAGE_AGENT GÜNCELLEMESİ ===\n" + report_update
        result_state["final_report"] = current_report
        
    return result_state

from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

def runtime_xss_agent(state: ScannerState) -> dict:
    """
    dynamic agent: runtime_xss_agent
    """
    llm = get_llm()
    network_traffic = state.get("network_traffic", [])
    if not network_traffic:
        return {"current_phase": "dynamic_done"}
        
    system_prompt = """Sen bir Dinamik XSS Uzmanısın.
Görevin ağ isteklerinden yansıyan payload'ların (Reflected XSS) WebView veya UI katmanında çalışıp çalışmadığını gösteren işaretleri yakalamaktır.
    
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
    context_text += f"\n--- AĞ TRAFİĞİ ---\n{json.dumps(network_traffic, indent=2)}\n"
    
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
                    f["source_agent"] = "runtime_xss_agent" 
        elif isinstance(parsed, dict) and "report_update" in parsed:
            report_update = parsed["report_update"]
        elif isinstance(parsed, dict) and "mapped_findings" in parsed: # OWASP special
            report_update = json.dumps(parsed, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"[runtime_xss_agent] JSON parse hatası: {e}")

    result_state = {"current_phase": "dynamic_done"}
    if new_findings:
        current_findings = state.get("findings", [])
        current_findings.extend(new_findings)
        result_state["findings"] = current_findings
        
    if report_update:
        current_report = state.get("final_report", "")
        current_report += f"\n\n=== RUNTIME_XSS_AGENT GÜNCELLEMESİ ===\n" + report_update
        result_state["final_report"] = current_report
        
    return result_state

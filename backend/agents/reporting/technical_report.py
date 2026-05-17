from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

def technical_report_agent(state: ScannerState) -> dict:
    """
    reporting agent: technical_report_agent
    """
    llm = get_llm()
    findings = state.get("findings", [])
    if not findings:
        return {"current_phase": "reporting_done"}
        
    system_prompt = """Sen bir Teknik Raporlama Uzmanısın.
Görevin tespit edilen zafiyetlerin yeniden üretilmesi (steps to reproduce) için detaylı teknik adımları içeren bir rapor taslağı oluşturmaktır.
    
Bulgularını aşağıdaki JSON formatında döndürmelisin:
    {
      "report_update": "Genişletilmiş veya güncellenmiş metin..."
    }
    Sadece JSON döndür.
    """
    
    context_text = ""
    context_text += f"\n--- BULGULAR ---\n{json.dumps(findings, indent=2)}\n"
    
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
        elif isinstance(parsed, dict) and "report_update" in parsed:
            report_update = parsed["report_update"]
        elif isinstance(parsed, dict) and "mapped_findings" in parsed: # OWASP special
            report_update = json.dumps(parsed, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"[technical_report_agent] JSON parse hatası: {e}")

    result_state = {"current_phase": "reporting_done"}
    if new_findings:
        current_findings = state.get("findings", [])
        current_findings.extend(new_findings)
        result_state["findings"] = current_findings
        
    if report_update:
        current_report = state.get("final_report", "")
        current_report += f"\n\n=== TECHNICAL_REPORT_AGENT GÜNCELLEMESİ ===\n" + report_update
        result_state["final_report"] = current_report
        
    return result_state

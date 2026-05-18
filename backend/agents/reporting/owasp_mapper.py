from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

def owasp_mapper_agent(state: ScannerState) -> dict:
    """
    Raporlama ajanı: Tüm ajanlardan gelen bulguları (findings) alır ve OWASP Mobile Top 10 ile eşleştirir.
    Nihai raporu oluşturarak UI tarafındaki JSON parse işlemlerini tetikler.
    """
    llm = get_llm()
    findings = state.get("findings", [])
    
    if not findings:
        return {"final_report": json.dumps({"executive_summary": "Herhangi bir zafiyet bulunamadı.", "mapped_findings": []}), "current_phase": "done"}
        
    system_prompt = """
    Sen bir OWASP Mobile Güvenlik Uzmanısın.
    Görevin sana verilen zafiyet listesini incelemek ve her bir zafiyeti güncel OWASP Mobile Top 10 (M1 - M10) kategorilerinden en uygun olanı ile eşleştirmektir.
    Ayrıca yöneticiler için kısa bir 'Executive Summary' (Yönetici Özeti) oluşturmalısın.
    
    Lütfen aşağıdaki JSON formatında bir çıktı üret:
    {
      "executive_summary": "Tüm bulguların yöneticiler için teknik olmayan genel özeti...",
      "mapped_findings": [
        {
          "vulnerability_name": "...",
          "owasp_category": "M1: Improper Platform Usage",
          "severity": "...",
          "description": "...",
          "remediation": "..."
        }
      ]
    }
    Sadece JSON döndür.
    """
    
    findings_text = json.dumps(findings, indent=2)
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"İşte sistemdeki diğer ajanlardan gelen bulgular:\n{findings_text}")
    ])
    
    final_report_str = response.content
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        final_report_json = json.loads(content)
        # Frontend'in okuyabilmesi için JSON string olarak set ediyoruz.
        final_report_str = json.dumps(final_report_json, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"OWASPMapperAgent JSON parse hatası: {e}")
        # Hata durumunda frontend'in çökmemesi için varsayılan json döner
        final_report_str = json.dumps({
            "executive_summary": "Rapor oluşturulurken bir hata meydana geldi.",
            "mapped_findings": []
        })
        
    return {
        "final_report": final_report_str,
        "current_phase": "done"
    }

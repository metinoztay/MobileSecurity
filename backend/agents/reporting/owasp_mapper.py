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
        empty_report = {"executive_summary": "Herhangi bir zafiyet bulunamadı.", "mapped_findings": []}
        return {"final_report": json.dumps({"static_report": empty_report, "dynamic_report": empty_report}), "current_phase": "done"}
        
    system_prompt = """
    Sen bir OWASP Mobile Güvenlik Uzmanısın.
    Görevin sana verilen zafiyet listesini incelemek ve her bir zafiyeti güncel OWASP Mobile Top 10 (M1 - M10) kategorilerinden en uygun olanı ile eşleştirmektir.
    Zafiyetleri kaynağına göre (Statik Ajanlar vs Dinamik Ajanlar) iki ayrı rapora ayırmalısın.
    
    Lütfen aşağıdaki JSON formatında bir çıktı üret:
    {
      "static_report": {
        "executive_summary": "Statik analiz bulgularının yöneticiler için kısa özeti...",
        "mapped_findings": [
          {
            "vulnerability_name": "...",
            "owasp_category": "M1: Improper Platform Usage",
            "severity": "...",
            "description": "...",
            "remediation": "...",
            "code_snippet": "...",
            "line_number": "..."
          }
        ]
      },
      "dynamic_report": {
        "executive_summary": "Dinamik analiz bulgularının yöneticiler için kısa özeti...",
        "mapped_findings": [
          {
            "vulnerability_name": "...",
            "owasp_category": "M3: Insecure Communication",
            "severity": "...",
            "description": "...",
            "remediation": "...",
            "code_snippet": "...",
            "line_number": "..."
          }
        ]
      }
    }
    ÖNEMLİ: Lütfen tüm çıktılarını, zafiyet isimlerini, açıklamaları ve çözüm önerilerini tamamen Türkçe (Turkish) olarak üret.
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
        empty_report = {"executive_summary": "Rapor oluşturulurken bir hata meydana geldi.", "mapped_findings": []}
        final_report_str = json.dumps({
            "static_report": empty_report,
            "dynamic_report": empty_report
        })
        
    return {
        "final_report": final_report_str,
        "current_phase": "done"
    }

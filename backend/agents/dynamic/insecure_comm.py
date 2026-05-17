from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

def insecure_comm_agent(state: ScannerState) -> dict:
    """
    Dinamik analiz ajanı: Ağ trafiğini inceler, güvensiz iletişim (cleartext, pinleme eksikliği) arar.
    """
    llm = get_llm()
    network_traffic = state.get("network_traffic", [])
    
    if not network_traffic:
        return {"current_phase": "dynamic_comm_done"}
        
    system_prompt = """
    Sen bir Dinamik Mobil Ağ Trafiği Güvenlik Uzmanısın.
    Görevin sana verilen yakalanmış ağ trafiği (HTTP/HTTPS) loglarını inceleyerek güvensiz iletişim zafiyetlerini (Örn: Düz metin HTTP kullanımı, Sertifika Pinleme eksikliği göstergeleri, URL'de taşınan hassas veriler) tespit etmektir.
    
    Bulgularını aşağıdaki JSON formatında bir liste olarak döndürmelisin:
    [
      {
        "vulnerability_name": "Insecure Communication (HTTP)",
        "severity": "Medium",
        "description": "Detaylı açıklama",
        "affected_files": ["endpoint_url"],
        "remediation": "Çözüm önerisi"
      }
    ]
    Eğer zafiyet yoksa boş liste `[]` döndür. Sadece JSON döndür.
    """
    
    findings = []
    
    traffic_text = json.dumps(network_traffic, indent=2)
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"İşte ağ trafiği logları:\n{traffic_text}")
    ])
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        new_findings = json.loads(content)
        if isinstance(new_findings, list):
            findings.extend(new_findings)
    except Exception as e:
        print(f"InsecureCommAgent JSON parse hatası: {e}")

    current_findings = state.get("findings", [])
    current_findings.extend(findings)
    
    return {
        "findings": current_findings,
        "current_phase": "dynamic_comm_done"
    }

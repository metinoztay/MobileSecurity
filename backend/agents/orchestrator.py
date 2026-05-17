from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

def orchestrator_node(state: ScannerState) -> dict:
    """
    Sistemin beyni. Mevcut duruma bakar ve hangi ajanin calismasi gerektigine karar verir.
    """
    llm = get_llm()
    
    system_prompt = """
    Sen Mobil Güvenlik Platformunun Orkestratörüsün (Orchestrator).
    Görevin: Sistemdeki durumu (state) incelemek ve sıradaki çalışması gereken ajanı seçmektir.
    Sistemde hiçbir kural motoru yoktur, ajanların sırasına sen karar verirsin.
    
    Ajan Listesi:
    - hardcoded_secrets_agent : Kaynak kodlar okunmuşsa ve secret analizi yapılmamışsa bu ajanı çağır.
    - insecure_comm_agent : Ağ trafiği logları varsa ve iletişim güvenliği analizi yapılmamışsa çağır.
    - owasp_mapper_agent : Tüm analizler (statik ve dinamik) bitmişse ve bulgular (findings) varsa çağır.
    - END : İşlem tamamen bittiyse.
    
    Şu anki State verileri:
    - Phase: {current_phase}
    - Bulgular (Findings) Sayısı: {findings_count}
    - İncelenen Dosyalar: {files_count}
    - Ağ İstekleri Sayısı: {network_req_count}
    
    Lütfen sadece bir JSON objesi döndür: {{"next_agent": "ajan_adi"}}
    """
    
    # Check if we already did something. For simplicity, we just look at the state.
    # We will simulate a state machine that goes: hardcoded -> insecure_comm -> owasp_mapper -> END
    findings_count = len(state.get("findings", []))
    files_count = len(state.get("source_code", {}))
    network_req_count = len(state.get("network_traffic", []))
    current_phase = state.get("current_phase", "init")
    
    formatted_prompt = system_prompt.format(
        current_phase=current_phase,
        findings_count=findings_count,
        files_count=files_count,
        network_req_count=network_req_count
    )
    
    # We use LLM to decide the next route
    # In a real scenario, we pass more context
    response = llm.invoke([
        SystemMessage(content=formatted_prompt),
        HumanMessage(content="Sıradaki ajanı seç.")
    ])
    
    try:
        # LLM bazen markdown code block icinde json dondurebilir
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        decision = json.loads(content)
        next_agent = decision.get("next_agent", "END")
    except Exception as e:
        # Hata durumunda statik bir fallback veya hatayi loglama
        print(f"Orkestratör JSON parse hatası: {e}. Yanıt: {response.content}")
        next_agent = "END"
        
    return {"next_agent": next_agent}

# backend/agents/orchestrator.py

from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

AGENT_LIST = [
    "manifest_analyzer_agent", "hardcoded_secrets_agent", "crypto_analyzer_agent",
    "insecure_storage_agent", "network_config_agent", "webview_security_agent",
    "deeplink_analyzer_agent", "intent_spoofing_agent", "broadcast_receiver_agent",
    "content_provider_agent", "service_analyzer_agent",
    "insecure_comm_agent", "auth_bypass_agent", "data_leakage_agent",
    "runtime_sqli_agent", "runtime_xss_agent", "session_management_agent",
    "severity_scoring_agent", "remediation_agent", "executive_summary_agent",
    "technical_report_agent", "owasp_mapper_agent"
]

def orchestrator_node(state: ScannerState) -> dict:
    """
    Sistemin beyni. Mevcut duruma bakar ve hangi ajanin calismasi gerektigine karar verir.
    Tamamlanan ajanlari 'completed_agents' listesinde tutarak sonsuz donguyu engeller.
    """
    llm = get_llm()
    completed = state.get("completed_agents", [])
    
    # Tüm olasi ajanlar
    all_agents = AGENT_LIST
    
    # Henüz çalışmayanlar
    pending_agents = [a for a in all_agents if a not in completed]
    
    if not pending_agents:
        # Eger calisacak ajan kalmadiysa islemi bitir
        return {"next_agent": "END"}
        
    system_prompt = """
    Sen Mobil Güvenlik Platformunun Orkestratörüsün (Orchestrator).
    Görevin: Sistemdeki durumu (state) incelemek ve henüz çalışmamış ajanlar arasından sıradaki çalışması gereken ajanı seçmektir.
    Sistemde hiçbir kural motoru yoktur, ajanların sırasına sen karar verirsin.
    Ancak mantıksal bir sıra izlemelisin: Önce statik analizler, sonra dinamik analizler, en son raporlama analizleri.
    
    Henüz Çalışmamış Ajanlar (Sadece bunlardan birini seçebilirsin!):
    {pending_agents}
    
    Şu anki State verileri:
    - Phase: {current_phase}
    - Bulgular (Findings) Sayısı: {findings_count}
    - İncelenen Dosyalar: {files_count}
    - Ağ İstekleri Sayısı: {network_req_count}
    
    Lütfen sadece bir JSON objesi döndür: {{"next_agent": "ajan_adi"}}
    Eğer tüm analizlerin bittiğini düşünüyorsan {{"next_agent": "END"}} döndürebilirsin.
    """
    
    findings_count = len(state.get("findings", []))
    files_count = len(state.get("source_code", {}))
    network_req_count = len(state.get("network_traffic", []))
    current_phase = state.get("current_phase", "init")
    
    formatted_prompt = system_prompt.format(
        pending_agents=", ".join(pending_agents),
        current_phase=current_phase,
        findings_count=findings_count,
        files_count=files_count,
        network_req_count=network_req_count
    )
    
    response = llm.invoke([
        SystemMessage(content=formatted_prompt),
        HumanMessage(content="Sıradaki ajanı seç (Sadece belirtilen listeden).")
    ])
    
    next_agent = "END"
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        decision = json.loads(content)
        next_agent = decision.get("next_agent", "END")
    except Exception as e:
        print(f"Orkestratör JSON parse hatası: {e}. Yanıt: {response.content}")
        if pending_agents:
            next_agent = pending_agents[0]
            
    # Eğer model listede olmayan bir şey üretmişse (hallucination), zorla listeden al
    if next_agent != "END" and next_agent not in pending_agents:
        next_agent = pending_agents[0]
        
    if next_agent != "END":
        completed.append(next_agent)
        
    return {
        "next_agent": next_agent,
        "completed_agents": completed,
        "current_phase": "processing"
    }

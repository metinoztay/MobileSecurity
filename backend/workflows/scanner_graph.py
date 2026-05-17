from langgraph.graph import StateGraph, END
from backend.core.state import ScannerState
from backend.agents.orchestrator import orchestrator_node
from backend.agents.static.hardcoded_secrets import hardcoded_secrets_agent
from backend.agents.dynamic.insecure_comm import insecure_comm_agent
from backend.agents.reporting.owasp_mapper import owasp_mapper_agent

def create_scanner_graph():
    """
    Sistemin ana LangGraph iş akışını (workflow) oluşturur.
    Tüm yönlendirmeler (routing) Orchestrator üzerinden dinamik olarak yapılır.
    """
    workflow = StateGraph(ScannerState)
    
    # Düğümleri (Ajanları) ekle
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("hardcoded_secrets_agent", hardcoded_secrets_agent)
    workflow.add_node("insecure_comm_agent", insecure_comm_agent)
    workflow.add_node("owasp_mapper_agent", owasp_mapper_agent)
    
    # Başlangıç noktası Orkestratör'dür
    workflow.set_entry_point("orchestrator")
    
    # Yönlendirme fonksiyonu: Orkestratörün state üzerindeki 'next_agent' değerini okur
    def route_from_orchestrator(state: ScannerState) -> str:
        next_agent = state.get("next_agent", "END")
        if next_agent == "END":
            return "end"
        return next_agent

    # Orkestratörden çıkış yönlendirmeleri
    workflow.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "hardcoded_secrets_agent": "hardcoded_secrets_agent",
            "insecure_comm_agent": "insecure_comm_agent",
            "owasp_mapper_agent": "owasp_mapper_agent",
            "end": END
        }
    )
    
    # Her ajan işini bitirdikten sonra tekrar Orkestratöre döner (Merkezi Kontrol)
    workflow.add_edge("hardcoded_secrets_agent", "orchestrator")
    workflow.add_edge("insecure_comm_agent", "orchestrator")
    workflow.add_edge("owasp_mapper_agent", "orchestrator")
    
    return workflow.compile()

# backend/workflows/scanner_graph.py

from langgraph.graph import StateGraph, END
from backend.core.state import ScannerState
from backend.agents.orchestrator import orchestrator_node

from backend.agents.static.decompile_agent import decompile_agent

# --- Statik Ajanlar ---
from backend.agents.static.manifest_analyzer import manifest_analyzer_agent
from backend.agents.static.hardcoded_secrets import hardcoded_secrets_agent
from backend.agents.static.crypto_analyzer import crypto_analyzer_agent
from backend.agents.static.insecure_storage import insecure_storage_agent
from backend.agents.static.network_config import network_config_agent
from backend.agents.static.webview_security import webview_security_agent
from backend.agents.static.deeplink_analyzer import deeplink_analyzer_agent
from backend.agents.static.intent_spoofing import intent_spoofing_agent
from backend.agents.static.broadcast_receiver import broadcast_receiver_agent
from backend.agents.static.content_provider import content_provider_agent
from backend.agents.static.service_analyzer import service_analyzer_agent

# --- Dinamik Ajanlar ---
from backend.agents.dynamic.insecure_comm import insecure_comm_agent
from backend.agents.dynamic.auth_bypass import auth_bypass_agent
from backend.agents.dynamic.data_leakage import data_leakage_agent
from backend.agents.dynamic.runtime_sqli import runtime_sqli_agent
from backend.agents.dynamic.runtime_xss import runtime_xss_agent
from backend.agents.dynamic.session_management import session_management_agent

# --- Raporlama Ajanları ---
from backend.agents.reporting.severity_scoring import severity_scoring_agent
from backend.agents.reporting.remediation import remediation_agent
from backend.agents.reporting.executive_summary import executive_summary_agent
from backend.agents.reporting.technical_report import technical_report_agent
from backend.agents.reporting.owasp_mapper import owasp_mapper_agent


AGENT_LIST = [
    "decompile_agent",
    "manifest_analyzer_agent", "hardcoded_secrets_agent", "crypto_analyzer_agent",
    "insecure_storage_agent", "network_config_agent", "webview_security_agent",
    "deeplink_analyzer_agent", "intent_spoofing_agent", "broadcast_receiver_agent",
    "content_provider_agent", "service_analyzer_agent",
    "insecure_comm_agent", "auth_bypass_agent", "data_leakage_agent",
    "runtime_sqli_agent", "runtime_xss_agent", "session_management_agent",
    "severity_scoring_agent", "remediation_agent", "executive_summary_agent",
    "technical_report_agent", "owasp_mapper_agent"
]

def create_scanner_graph():
    workflow = StateGraph(ScannerState)
    
    # 1. Orkestratör düğümünü ekle
    workflow.add_node("orchestrator", orchestrator_node)
    
    # 2. Tüm ajanları tek tek düğüm olarak ekle
    workflow.add_node("decompile_agent", decompile_agent)
    workflow.add_node("manifest_analyzer_agent", manifest_analyzer_agent)
    workflow.add_node("hardcoded_secrets_agent", hardcoded_secrets_agent)
    workflow.add_node("crypto_analyzer_agent", crypto_analyzer_agent)
    workflow.add_node("insecure_storage_agent", insecure_storage_agent)
    workflow.add_node("network_config_agent", network_config_agent)
    workflow.add_node("webview_security_agent", webview_security_agent)
    workflow.add_node("deeplink_analyzer_agent", deeplink_analyzer_agent)
    workflow.add_node("intent_spoofing_agent", intent_spoofing_agent)
    workflow.add_node("broadcast_receiver_agent", broadcast_receiver_agent)
    workflow.add_node("content_provider_agent", content_provider_agent)
    workflow.add_node("service_analyzer_agent", service_analyzer_agent)
    
    workflow.add_node("insecure_comm_agent", insecure_comm_agent)
    workflow.add_node("auth_bypass_agent", auth_bypass_agent)
    workflow.add_node("data_leakage_agent", data_leakage_agent)
    workflow.add_node("runtime_sqli_agent", runtime_sqli_agent)
    workflow.add_node("runtime_xss_agent", runtime_xss_agent)
    workflow.add_node("session_management_agent", session_management_agent)
    
    workflow.add_node("severity_scoring_agent", severity_scoring_agent)
    workflow.add_node("remediation_agent", remediation_agent)
    workflow.add_node("executive_summary_agent", executive_summary_agent)
    workflow.add_node("technical_report_agent", technical_report_agent)
    workflow.add_node("owasp_mapper_agent", owasp_mapper_agent)
    
    # Başlangıç noktası Orkestratör'dür
    workflow.set_entry_point("orchestrator")
    
    # Yönlendirme fonksiyonu: Orkestratörün kararı
    def route_from_orchestrator(state: ScannerState) -> str:
        next_agent = state.get("next_agent", "END")
        if next_agent == "END" or next_agent not in AGENT_LIST:
            return "end"
        return next_agent

    # Orkestratörden çıkış yönlendirmeleri (conditional edges)
    routing_dict = {name: name for name in AGENT_LIST}
    routing_dict["end"] = END
    
    workflow.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        routing_dict
    )
    
    # Her ajan işini bitirdikten sonra tekrar Orkestratöre döner
    for agent_name in AGENT_LIST:
        workflow.add_edge(agent_name, "orchestrator")
    
    return workflow.compile()

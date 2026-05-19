from typing import TypedDict, List, Dict, Any

class Finding(TypedDict):
    vulnerability_name: str
    severity: str
    description: str
    affected_files: List[str]
    remediation: str

class ScannerState(TypedDict):
    # Girdi Verileri
    scan_id: str
    apk_path: str
    source_code: Dict[str, str] # {dosya_yolu: icerik}
    network_traffic: List[Dict[str, Any]] # Yakalanan ag loglari
    
    # İslem Durumu
    current_phase: str # 'static', 'dynamic', 'reporting', 'done'
    next_agent: str # Orkestratörün karar verdiği bir sonraki ajan adi
    completed_agents: List[str] # Zaten calismis olan ajanlar listesi
    
    # Çıktı Verileri
    findings: List[Finding] # Ajanlarin buldugu zafiyetler
    final_report: str # Nihai owasp/yonetici raporu
    
    # Hata Yönetimi
    errors: List[str]

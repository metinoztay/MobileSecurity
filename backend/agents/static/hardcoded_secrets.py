from langchain_core.messages import HumanMessage, SystemMessage
from backend.core.state import ScannerState
from backend.core.llm_provider import get_llm
import json

def hardcoded_secrets_agent(state: ScannerState) -> dict:
    """
    Statik analiz ajanı: Kaynak kodda API key, token vb. arar.
    Regex kullanmaz, doğrudan LLM'in mantıksal analizini kullanır.
    """
    llm = get_llm()
    source_code = state.get("source_code", {})
    
    if not source_code:
        return {"current_phase": "static_secrets_done"}
        
    system_prompt = """
    Sen bir Mobil Uygulama Statik Analiz Güvenlik Uzmanısın.
    Görevin sana verilen kaynak kod dosyalarında "Hardcoded Secrets" (gömülü API anahtarları, şifreler, tokenlar vb.) bulmaktır.
    
    Bulgularını aşağıdaki JSON formatında bir liste olarak döndürmelisin:
    [
      {
        "vulnerability_name": "Hardcoded API Key",
        "severity": "High",
        "description": "Detaylı açıklama",
        "affected_files": ["dosya_yolu"],
        "remediation": "Çözüm önerisi"
      }
    ]
    Eğer zafiyet yoksa boş liste `[]` döndür. Sadece JSON döndür.
    """
    
    findings = []
    
    # Gerçek projede kaynak kodlar batch'ler halinde veya vektör veritabanı ile gönderilebilir.
    # Burada konsept kanıtı için metin olarak birleştiriyoruz.
    code_text = ""
    for path, content in source_code.items():
        code_text += f"\n--- DOSYA: {path} ---\n{content}\n"
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"İşte kaynak kodlar:\n{code_text}")
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
        print(f"HardcodedSecretAgent JSON parse hatası: {e}")

    # Mevcut findings ile birleştir
    current_findings = state.get("findings", [])
    current_findings.extend(findings)
    
    return {
        "findings": current_findings,
        "current_phase": "static_secrets_done"
    }

import os
import sys

# Proje kok dizinini PYTHONPATH'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.workflows.scanner_graph import create_scanner_graph
from backend.core.state import ScannerState

def main():
    print("🚀 Mobil Güvenlik Platformu (Multi-Agent LLM Mimarisi) Başlatılıyor...\n")
    
    # 1. State nesnesini başlat (Mock verilerle)
    initial_state = ScannerState(
        apk_path="/mock/path/app.apk",
        source_code={
            "MainActivity.java": "public class MainActivity { public static final String API_KEY = 'AKIAIOSFODNN7EXAMPLE'; }",
            "NetworkConfig.xml": "<network-security-config><base-config cleartextTrafficPermitted='true'/></network-security-config>"
        },
        network_traffic=[
            {
                "url": "http://api.example.com/login",
                "method": "POST",
                "headers": {"Authorization": "Basic YWRtaW46YWRtaW4="},
                "body": '{"username": "admin", "password": "password123"}'
            }
        ],
        findings=[],
        current_phase="init",
        next_agent="",
        completed_agents=[],
        final_report="",
        errors=[]
    )
    
    # 2. LangGraph'ı derle
    app = create_scanner_graph()
    
    # 3. Akışı çalıştır ve süreci izle
    print("🔍 Orkestratör analizi başlatıyor...\n")
    
    # Graph'i calistir. stream() bize adim adim state'i dondurur.
    config = {"recursion_limit": 20} # Sonsuz donguyu onlemek icin
    
    try:
        for output in app.stream(initial_state, config=config):
            for key, value in output.items():
                print(f"👉 Düğüm Çalıştı: {key}")
                if key == "orchestrator":
                    print(f"   Orkestratörün Yönlendirmesi: {value.get('next_agent')}")
                elif key == "owasp_mapper_agent":
                    print("\n📝 Rapor Hazırlandı.")
                print("-" * 50)
                
        # Final durumunu al
        # state'i en son adimdan almamiz lazim, veya invoke() kullanabiliriz
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

    print("\n✅ Analiz Tamamlandı! Raporu veya veritabanını kontrol edebilirsiniz.")

if __name__ == "__main__":
    # Test ortaminda env degiskenleri olmadigi icin sahte bir API key ile Langchain hata verebilir.
    # LLM cagrilarini gercekten yapmak isterseniz .env dosyasinda OPENAI_API_KEY veya GOOGLE_API_KEY ayarlayin.
    main()

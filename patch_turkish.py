import glob
import os

def patch_turkish():
    files = glob.glob('backend/agents/**/*.py', recursive=True)
    count = 0
    for filepath in files:
        if '__init__' in filepath or 'orchestrator' in filepath:
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'TÜRKÇE' in content or 'Türkçe' in content:
            print(f"Skipping {filepath}, already contains 'Türkçe'")
            continue
            
        target = "Sadece JSON döndür."
        if target in content:
            new_text = "ÖNEMLİ: Lütfen tüm çıktılarını, zafiyet isimlerini, açıklamaları ve çözüm önerilerini tamamen Türkçe (Turkish) olarak üret.\n    Sadece JSON döndür."
            content = content.replace(target, new_text)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Patched {filepath}")
            count += 1
        else:
            print(f"Could not find target in {filepath}")
            
    print(f"Total files patched: {count}")

if __name__ == '__main__':
    patch_turkish()

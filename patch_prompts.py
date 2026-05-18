import glob

def patch_prompts():
    files = glob.glob('backend/agents/static/*.py') + glob.glob('backend/agents/dynamic/*.py')
    for filepath in files:
        if 'decompile_agent.py' in filepath:
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '"code_snippet"' in content:
            continue
            
        old_pattern = '"affected_files": ["dosya_yolu"],'
        new_pattern = '"affected_files": ["dosya_yolu"],\n        "code_snippet": "Zafiyete neden olan kod parçasının (snippet) tam metni",\n        "line_number": "Bulunduğu satır numarası veya yeri (tahmini)",'
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
    print("Prompts patched to include code_snippet and line_number.")

if __name__ == '__main__':
    patch_prompts()

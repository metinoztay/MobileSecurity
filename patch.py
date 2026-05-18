import os
import glob

def run():
    files = glob.glob('backend/agents/static/*.py') + glob.glob('backend/agents/dynamic/*.py')
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        agent_name = os.path.basename(filepath).replace('.py', '_agent')
        
        if 'f["source_agent"]' in content:
            continue
            
        old_code = """        if isinstance(parsed, list):
            new_findings = parsed"""
                
        new_code = f"""        if isinstance(parsed, list):
            new_findings = parsed
            for f in new_findings:
                if isinstance(f, dict):
                    f["source_agent"] = "{agent_name}" """
                        
        content = content.replace(old_code, new_code)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    print("Patch successful!")

if __name__ == "__main__":
    run()

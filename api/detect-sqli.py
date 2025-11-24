
import re
import json

def analyze_sql_injection(filename):
    
    vulnerabilities = []
    
    patterns = [
        (r'`SELECT.*\$\{.*\}.*`', 'SQL Injection en SELECT'),
        (r'`INSERT.*\$\{.*\}.*`', 'SQL Injection en INSERT'),
        (r'`UPDATE.*\$\{.*\}.*`', 'SQL Injection en UPDATE'),
        (r'`DELETE.*\$\{.*\}.*`', 'SQL Injection en DELETE'),
        (r'`.*WHERE.*\$\{.*\}.*`', 'SQL Injection en WHERE clause'),
        (r'`.*ORDER BY.*\$\{.*\}.*`', 'SQL Injection en ORDER BY'),
    ]
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for pattern, description in patterns:
                if re.search(pattern, line):
                    vulnerabilities.append({
                        'line': line_num,
                        'code': line.strip(),
                        'type': description,
                        'severity': 'CRITICAL',
                        'cwe': 'CWE-89'
                    })
                    
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {filename}")
        return []
    
    return vulnerabilities

def main():
    filename = 'server-sqlite.js'
    print("="*60)
    print("ANÁLISIS SAST - SQL INJECTION DETECTOR")
    print("="*60)
    print(f"\nAnalizando: {filename}")
    print("-"*60)
    
    vulnerabilities = analyze_sql_injection(filename)
    
    if vulnerabilities:
        print(f"\n🚨 Se encontraron {len(vulnerabilities)} vulnerabilidades:\n")
        
        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"{i}. Línea {vuln['line']}: {vuln['type']}")
            print(f"   Severidad: {vuln['severity']}")
            print(f"   CWE: {vuln['cwe']}")
            print(f"   Código: {vuln['code'][:80]}...")
            print()
        
        with open('sast-results.json', 'w', encoding='utf-8') as f:
            json.dump(vulnerabilities, f, indent=2)
        print(f"✅ Resultados guardados en: sast-results.json")
        
        with open('sast-results.txt', 'w', encoding='utf-8') as f:
            f.write("ANÁLISIS SAST - SQL INJECTION DETECTOR\n")
            f.write("="*60 + "\n\n")
            for i, vuln in enumerate(vulnerabilities, 1):
                f.write(f"{i}. Línea {vuln['line']}: {vuln['type']}\n")
                f.write(f"   Severidad: {vuln['severity']}\n")
                f.write(f"   CWE: {vuln['cwe']}\n")
                f.write(f"   Código: {vuln['code']}\n\n")
        print(f"✅ Resultados guardados en: sast-results.txt")
        
    else:
        print("\n✅ No se encontraron vulnerabilidades.")
    
    print("\n" + "="*60)
    print(f"Total de vulnerabilidades encontradas: {len(vulnerabilities)}")
    print("="*60)

if __name__ == '__main__':
    main()
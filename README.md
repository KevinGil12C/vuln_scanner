# vuln_scanner# 🛡️ VulnScanner Pro

**Professional Open-Source Vulnerability Assessment Tool**

Una herramienta completa de análisis de vulnerabilidades, similar a Nessus pero completamente open-source, construida con Python y Eel.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

---

## 📋 Índice

- [Características](#-características)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Tipos de Escaneo](#-tipos-de-escaneo)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Ejemplos](#-ejemplos)
- [Advertencias Legales](#-advertencias-legales)
- [FAQ](#-faq)
- [Contribuir](#-contribuir)

---

## ✨ Características

### Escaneo de Red
- ✅ **Escaneo de puertos avanzado** (TCP Connect, SYN, Stealth)
- ✅ **Detección de servicios** con banner grabbing
- ✅ **Fingerprinting de OS** mediante análisis TTL
- ✅ **Escaneo paralelo** con ThreadPool (hasta 100 threads)
- ✅ **Rangos personalizables** de puertos (1-65535)

### Análisis de Vulnerabilidades
- ✅ **Base de datos CVE** integrada
- ✅ **Exploit database** cross-reference
- ✅ **Detección de versiones** vulnerable de software
- ✅ **Análisis de configuraciones** inseguras
- ✅ **Pruebas de credenciales** débiles
- ✅ **Vulnerabilidades web** (SQL Injection, XSS, CSRF)
- ✅ **Análisis SSL/TLS** completo

### Compliance & Reportes
- ✅ **Verificación de compliance** (PCI-DSS, HIPAA, CIS)
- ✅ **Reportes profesionales** (HTML, JSON, CSV)
- ✅ **Matriz de riesgo** detallada
- ✅ **Plan de remediación** priorizado
- ✅ **Scoring CVSS** automático

### Interfaz
- ✅ **UI moderna** con Bootstrap 5
- ✅ **Dashboard interactivo** con estadísticas
- ✅ **Historial de escaneos** persistente
- ✅ **Progreso en tiempo real**
- ✅ **100% Python** - sin servidor HTTP externo

---

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Sistema operativo: Windows, Linux, o macOS

### Paso 1: Clonar o Descargar

```bash
# Crear directorio del proyecto
mkdir VulnScanner
cd VulnScanner
```

### Paso 2: Crear Estructura de Carpetas

```bash
# Windows
mkdir web

# Linux/Mac
mkdir web
```

### Paso 3: Instalar Dependencias

```bash
pip install eel
```

**Dependencias opcionales** (para funciones avanzadas):
```bash
pip install requests  # Para análisis web
pip install paramiko  # Para SSH testing (opcional)
```

### Paso 4: Guardar Archivos

1. Guarda el contenido de `app.py` en la raíz del proyecto
2. Guarda el contenido de `index.html` dentro de la carpeta `web/`

### Estructura Final

```
VulnScanner/
├── app.py              # Backend Python
└── web/
    └── index.html      # Frontend
```

---

## ▶️ Uso

### Inicio Rápido

```bash
python app.py
```

La aplicación se abrirá automáticamente en tu navegador predeterminado.

### Interfaz Web

1. **Dashboard**: Vista general de seguridad
2. **New Scan**: Configurar y lanzar nuevos escaneos
3. **Results**: Análisis detallado de vulnerabilidades
4. **Compliance**: Estado de cumplimiento normativo
5. **History**: Historial de escaneos anteriores
6. **About**: Información de la herramienta

### Configurar un Escaneo

#### 1. Target (Objetivo)
```
Ejemplos:
- 192.168.1.1
- scanme.nmap.org
- example.com
```

#### 2. Port Range (Rango de Puertos)
- **Quick Scan**: 1-100 (Rápido)
- **Standard**: 1-1000 (Recomendado)
- **Extended**: 1-10000 (Completo)
- **Full**: 1-65535 (Exhaustivo)
- **Custom**: Personalizado (ej: 80,443,8080)

#### 3. Scan Type (Tipo de Escaneo)
- **TCP Connect**: Escaneo completo de conexión
- **SYN Scan**: Escaneo semi-abierto (requiere privilegios)
- **Stealth Scan**: Escaneo sigiloso con delays

#### 4. Scan Level (Nivel)
- **Quick**: Verificaciones básicas
- **Standard**: Análisis estándar (recomendado)
- **Full**: Incluye pruebas de credenciales
- **Comprehensive**: Todas las pruebas disponibles

#### 5. Opciones
- ☑️ OS Detection
- ☑️ Vulnerability Analysis
- ☑️ SSL/TLS Check
- ☑️ Compliance Check
- ☑️ Web Vulnerability Scan

---

## 🎯 Tipos de Escaneo

### 1. Network Scanning
```python
# Detecta:
- Puertos abiertos (TCP/UDP)
- Servicios en ejecución
- Versiones de software
- Banners de servicios
```

### 2. Vulnerability Assessment
```python
# Identifica:
- CVEs conocidos
- Exploits públicos
- Configuraciones inseguras
- Software desactualizado
```

### 3. Web Application Testing
```python
# Prueba:
- SQL Injection
- Cross-Site Scripting (XSS)
- CSRF vulnerabilities
- Security headers
- Sensitive directories
```

### 4. SSL/TLS Analysis
```python
# Verifica:
- Certificados válidos/expirados
- Protocolos obsoletos (SSLv3, TLS 1.0)
- Cipher suites débiles
- Configuración TLS
```

### 5. Authentication Testing
```python
# Evalúa:
- Credenciales por defecto
- Contraseñas débiles
- Anonymous access
- Fuerza bruta básica
```

### 6. Compliance Checking
```python
# Estándares:
- PCI-DSS
- HIPAA
- CIS Benchmarks
```

---

## 📊 Ejemplos de Uso

### Ejemplo 1: Escaneo Rápido
```
Target: 192.168.1.1
Port Range: 1-100
Scan Type: TCP Connect
Level: Quick
Options: OS Detection ✓
```
**Tiempo estimado**: 30 segundos

### Ejemplo 2: Análisis Completo
```
Target: example.com
Port Range: 1-1000
Scan Type: TCP Connect
Level: Full
Options: Todas ✓
```
**Tiempo estimado**: 5-10 minutos

### Ejemplo 3: Escaneo Web
```
Target: website.com
Port Range: 80,443,8080,8443
Scan Type: TCP Connect
Level: Comprehensive
Options: SSL Check ✓, Web Scan ✓
```
**Tiempo estimado**: 2-5 minutos

---

## 📁 Estructura del Proyecto

```
VulnScanner/
│
├── app.py                      # Backend Principal
│   ├── Port Scanning Functions
│   ├── Vulnerability Analysis
│   ├── CVE Database
│   ├── Exploit Matching
│   ├── SSL/TLS Analysis
│   ├── Compliance Checking
│   ├── Report Generation
│   └── Eel Integration
│
└── web/
    └── index.html              # Frontend UI
        ├── Bootstrap 5
        ├── JavaScript ES6
        ├── Dashboard
        ├── Scan Configuration
        ├── Results Visualization
        └── Export Functions
```

---

## 🔍 Base de Datos de Vulnerabilidades

### CVE Database Incluida
```python
- Apache (2.2, 2.4)
- OpenSSH (7.4, 7.x)
- Nginx (1.0, 1.10)
- MySQL (5.5, 5.x)
- ProFTPD (1.3.5)
```

### Exploit Database
```python
- FTP (vsftpd, ProFTPD)
- SSH (OpenSSH)
- MySQL
- Web Services
```

### Servicios Detectados
```
HTTP/HTTPS, FTP, SSH, Telnet, SMTP, POP3, IMAP,
MySQL, PostgreSQL, MongoDB, Redis, SMB, RDP, VNC,
DNS, TFTP, NFS, Oracle, MSSQL
```

---

## 📤 Exportación de Reportes

### Formatos Disponibles

#### 1. JSON
```json
{
  "scan_id": "20250112_143022",
  "target": "192.168.1.1",
  "vulnerabilities": [...],
  "summary": {...}
}
```

#### 2. HTML
```html
<!DOCTYPE html>
<html>
  <!-- Reporte profesional con estilos -->
  <!-- Tablas, gráficos, estadísticas -->
</html>
```

#### 3. CSV
```csv
Severity,Port,Service,Vulnerability,CVSS
Critical,21,FTP,Anonymous Login,9.5
High,80,HTTP,Missing Headers,7.5
```

---

## ⚠️ Advertencias Legales

### 🚨 IMPORTANTE - LEER ANTES DE USAR

**VulnScanner Pro es una herramienta de seguridad profesional.**

### Uso Legal
✅ **PERMITIDO:**
- Escanear tus propios sistemas
- Escanear con autorización escrita explícita
- Uso en entornos de laboratorio/testing
- Propósitos educativos en sistemas propios

❌ **PROHIBIDO:**
- Escanear sistemas sin autorización
- Uso para actividades ilegales
- Ataques maliciosos
- Explotación de vulnerabilidades encontradas

### Responsabilidad
```
El usuario es 100% responsable del uso de esta herramienta.
Los desarrolladores NO se hacen responsables de:
- Uso indebido o ilegal
- Daños causados a sistemas
- Violaciones de leyes locales
- Consecuencias legales derivadas del uso

SIEMPRE obtén autorización por escrito antes de escanear.
```

### Leyes Aplicables
```
USA: Computer Fraud and Abuse Act (CFAA)
EU: GDPR, Cybercrime Directive
México: Código Penal Federal - Delitos Informáticos
España: Código Penal Art. 197, 264
Argentina: Ley 26.388
```

---

## 🔧 Configuración Avanzada

### Personalizar Threads
```python
# En app.py, línea ~50
threads = 100  # Cambiar según CPU
```

### Timeout de Conexión
```python
# En app.py, función tcp_connect_scan
sock.settimeout(0.5)  # Ajustar timeout
```

### Agregar CVEs Personalizados
```python
CVE_DATABASE = {
    "YourSoftware/1.0": [
        {
            "cve": "CVE-2024-XXXXX",
            "severity": "Critical",
            "desc": "Description"
        }
    ]
}
```

---

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'eel'"
```bash
# Solución:
pip install eel
```

### Problema: "Port already in use"
```bash
# Solución: Eel usa puerto aleatorio automáticamente
# Si persiste, cerrar otras instancias de la app
```

### Problema: Escaneo muy lento
```python
# Solución: Reducir rango de puertos o aumentar threads
threads = 200  # En advanced_port_scan()
```

### Problema: "Permission denied" en puertos bajos
```bash
# En Linux/Mac para escanear puertos < 1024:
sudo python app.py
```

---

## 💡 FAQ

**P: ¿Es legal usar esta herramienta?**
R: Sí, siempre que tengas autorización para escanear el objetivo.

**P: ¿Necesito ser root/admin?**
R: No para la mayoría de funciones. Solo para SYN scan y puertos < 1024.

**P: ¿Funciona en Windows?**
R: Sí, completamente compatible con Windows, Linux y macOS.

**P: ¿Puedo agregar más CVEs?**
R: Sí, edita la variable CVE_DATABASE en app.py.

**P: ¿Qué tan preciso es?**
R: Similar a Nessus en detección básica. Para producción considera herramientas comerciales.

**P: ¿Detecta 0-days?**
R: No. Solo detecta vulnerabilidades conocidas en bases de datos públicas.

**P: ¿Puedo usarlo en pentesting profesional?**
R: Sí, pero complementa con otras herramientas (Nmap, Metasploit, Burp).

---

## 🤝 Contribuir

### Cómo Contribuir
1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Ideas para Contribuir
- Agregar más CVEs a la base de datos
- Implementar nuevos tipos de escaneo
- Mejorar detección de OS
- Añadir más exportadores (PDF, XML)
- Traducir a más idiomas
- Optimizar rendimiento

---

## 📝 Changelog

### v1.0.0 (2025-01-12)
- ✨ Lanzamiento inicial
- 🎯 Escaneo de puertos TCP
- 🔍 Base de datos CVE
- 📊 Reportes HTML/JSON/CSV
- 🛡️ Compliance checking
- 🌐 Interfaz web Bootstrap 5

---

## 📄 Licencia

```
MIT License

Copyright (c) 2025 VulnScanner Pro

Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia
de este software y archivos de documentación asociados, para usar el Software
sin restricciones, incluyendo sin limitación los derechos de usar, copiar, 
modificar, fusionar, publicar, distribuir, sublicenciar, y/o vender copias del
Software, sujeto a las siguientes condiciones:

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO.
```

---

## 🙏 Agradecimientos

- Bootstrap Team por la interfaz UI
- Eel Framework por la integración Python-JavaScript
- NIST por la base de datos CVE
- Comunidad de seguridad open-source

---

## 📞 Contacto

- 📧 Email: vuln-scanner@example.com
- 🌐 GitHub: github.com/vulnscanner
- 💬 Discord: discord.gg/vulnscanner

---

## ⭐ Soporte

Si te gusta este proyecto:
- ⭐ Dale una estrella en GitHub
- 🐛 Reporta bugs
- 💡 Sugiere mejoras
- 📢 Comparte con otros

---

**Desarrollado con ❤️ para la comunidad de seguridad**

**Happy Ethical Hacking! 🛡️**
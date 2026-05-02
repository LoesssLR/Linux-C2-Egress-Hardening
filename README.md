# Avance - Exposición (Seguridad de TI)

## Entorno Virtual (VirtualBox)
* **VM1** → Kali Linux (atacante). `192.168.199.130`
* **VM2** → Ubuntu Desktop (víctima). `192.168.199.131`
* **Adaptador 1:** NAT (internet).
* **Adaptador 2:** Red interna ("intnet").

*Ambas con acceso a Internet y dirección IP.*

## Credenciales

**Kali Linux**
* Usuario: `kali`
* Contraseña: `kali`

**Victima**
* Usuario: `victima`
* Contraseña: `victima-123`

## Descarga de Kali Linux
* **Enlace:** [https://www.kali.org/get-kali/#kali-platforms](https://www.kali.org/get-kali/#kali-platforms)
* **Plataforma:** VirtualMachines.
* **Software:** VirtualBox.

---

## Razon por la que no lo hice con Windows
- **Windows Defender:** Habría tenido que desactivarlo, y siento que el ataque hubiera tenido algo de sentido.

### Formas de evadirlo:
- **Ofuscación:** Hacer que el código sea ilegible para el antivirus y humanos, pero que aun así la computadora pueda ejecutarlo. Y lo que se hace específicamente es cambiar el nombres de las variables por cadenas aleatorias, se codifican los comandos en Base64 o se usan operaciones matemáticas (como XOR) para ocultar las direcciones IP y los comandos clave.
- **Encriptación y Empaquetado (Crypters):** El malware se encripta (por ejemplo, con AES). El archivo que se envía a la víctima solo contiene un pequeño programa legítimo (el "stub") y un bloque de datos cifrados. Cuando se ejecuta, el stub desencripta el malware directamente en la memoria RAM y lo ejecuta desde ahí, y hace que evite tocar el disco duro.
- **Ataques "Fileless" (Sin archivo):** En lugar de enviar un `.exe`, el atacante usa herramientas que ya están instaladas en Windows (conocidas como Living off the Land o LOLBins). Un documento PDF con un script podría lanzar un comando de PowerShell legítimo que descargue el backdoor directamente en la memoria.

### Respuesta de Microsoft a la forma de evadirlo:
**AMSI (Antimalware Scan Interface)**.
Incluso si un atacante ofusca su script, en algún momento el código tiene que desofuscarse para poder ejecutarse. AMSI se sitúa justo en ese punto: lee el código limpio justo milisegundos antes de que el motor de Windows lo ejecute y lo bloquea si detecta intenciones maliciosas.

---

## Backdoor
Bueno, según lo que investigué, un backdoor es un método o software que nos permite acceder a un sistema evitando los controles de seguridad normales.

* **Técnica utilizada:** ReverseShell con Python.

### Explicación principal:
* **Ataque Tradicional (Bind Shell):** El virus abre un puerto en la Víctima (en este caso 4444). El atacante escanea a la victima, ve el puerto abierto y entra.
  * *Problema:* Los firewalls modernos bloquean casi todas las entradas sospechosas.
* **Mi Ataque (Reverse Shell):** El puerto se abre en la maquina del atacante. El virus en la máquina victima le dice al SO (Ubuntu): "Conéctate a la IP `.130` en el puerto `4444`".
  * *Esto es mejor porque:* Para el firewall de Ubuntu, esto parece una "salida de internet" normal (como entrar a Google), y los firewalls suelen ser más permisivos con las conexiones salientes.

### Formas en las que se puede presentar un Backdoor
- **Ingeniería Social:** Correos (Phishing), mensajes de WhatsApp o Telegram con archivos adjuntos que parecen facturas, premios o documentos urgentes.
- **Malware / Troyanos:** Programas que parecen legítimos (un activador de Office, un juego "crackeado", un PDF reader gratuito) pero que traen el script de Python oculto en su interior.
- **Medios Físicos (BadUSB):** Un USB que dejas "olvidado" en una oficina. Al conectarlo, el dispositivo actúa como un teclado ultrarrápido que escribe y ejecuta el comando del backdoor en segundos.
- **Explotación de Vulnerabilidades (RCE):** Si el servidor de la víctima tiene un software desactualizado, puedes usar un exploit para ejecutar código de forma remota (Remote Code Execution) y forzar la ejecución del Reverse Shell sin que el usuario haga clic en nada.
- **Ataques de Cadena de Suministro (Supply Chain):** Modificar una librería de código abierto que otros desarrolladores usan, para que cuando ellos compilen su programa, el backdoor se incluya automáticamente.

---

## Paso a paso

### Kali Linux - Terminal 1
```bash
cd expo-backdoor
```

**Pasos por si hay que volver a empaquetar el .py:**
```bash
pyinstaller --onefile --noconsole SysUpdate.py
mv dist/SysUpdate .
staticx SysUpdate SysUpdate_Static
ls -lh SysUpdate_Static
```

**1. Descubrimiento de la Red**
*(Asumiendo que contamos con la dirección de red, pero no la especifica a la que vamos a ingresar).*
```bash
nmap -sn 192.168.199.0/24
```

**2. Auditoría de Puertos Externos**
*(Indica que todos los puertos están cerrados, como los de HTTP, FTP, SSH, por lo que no están aceptando conexiones remotas).*
```bash
nmap -Pn 192.168.199.131
```

**3. Revisar que el puerto especifico esté cerrado**
*(El puerto 4444 TCP/UDP será usado de ejemplo).*
```bash
nmap -Pn -p 4444 192.168.199.131
```

**4. Levantar el server para que se pueda descargar el parche.**
```bash
sudo python3 -m http.server 80
```
> **Nmap**: Herramienta estándar para descubrimiento de servicios, descubrir hosts que están activos, ver puertos abiertos y demás.

**En caso de volver a empezar el proceso:**
```bash
rm -rf build dist SysUpdate SysUpdate.spec
```

### Kali Linux - Terminal 2 (Esperando la conexión)
```bash
socat TCP-L:4444 -
```
> **Socat**: Herramienta muy poderosa para conexiones de red, más flexible que netcat, muy usada en seguridad ofensiva.

---

### Redactar correo (De mi cuenta principal a la secundaria)
* **Correo:** luisalelr.dev@gmail.com
* **Asunto:** URGENTE: Mitigación de Vulnerabilidades Críticas en Estaciones Linux de la Empresa.

**Mensaje:**
> Hola Roberto,
>
> Nuestro sistema de monitoreo ha detectado una serie de vulnerabilidades críticas que afectan la seguridad de tu estación de trabajo Ubuntu. Para mitigar estos riesgos, el equipo de Seguridad Informática está desplegando correcciones urgentes mediante parches de software.
>
> Es indispensable que apliques el siguiente parche de compatibilidad estática para asegurar tu equipo y evitar posibles filtraciones de datos. Este parche se encuentra alojado en el servidor interno de actualizaciones de la empresa, desde donde el departamento de TI distribuye las correcciones de seguridad para los equipos de la red corporativa.
>
> **Enlace de Descarga del Parche:** [http://192.168.199.130/SysUpdate_Static](http://192.168.199.130/SysUpdate_Static)
>
> **Instrucciones para la Instalación:**
> 1. Descarga el archivo `SysUpdate_Static`.
> 2. Haz clic derecho sobre el archivo en tu carpeta de Descargas -> Propiedades -> Permisos.
> 3. Activa la casilla 'Permitir ejecutar el archivo como un programa'.
> 4. Haz doble clic para ejecutar el parche. La corrección se aplicará automáticamente en segundo plano y, aproximadamente 10 segundos después, aparecerá un mensaje confirmando que el proceso se completó correctamente.
>
> Una vez finalizado, tu sistema estará protegido contra las vulnerabilidades detectadas.
>
> Saludos,
>
> **Departamento de Seguridad de la Información (TI).**

---

### En Ubuntu
Entrar a Gmail a ver el correo, poner el enlace en la URL para que se descargue el archivo, seguir los pasos y ejecutarlo.

Cuando se ejecuta, Kali Linux intercepta la conexión y queda dentro, comandos para probar:

```bash
whoami
cat /etc/hostname
notify-send "Actualización de seguridad instalada" "El sistema ha sido actualizado"
```

### Posibles mejoras
* **Escalada de Privilegios:** "Ahorita somos el usuario 'victima', pero podríamos intentar buscar archivos con permisos SUID o vulnerabilidades del Kernel para ser 'root'".
* **Agregar archivos o cosas que se puedan mostrar "muy sensibles" y verlas desde Kali.**
* **Ponerle un icono de una rueda de config al ejecutable de Ubuntu.**
* **Persistencia Real:** Un Reverse Shell normal se muere si la víctima reinicia la computadora. Un Backdoor real busca quedarse.
  * *Método:* Agregar el script de Python al crontab (tareas programadas) en Linux o al registro de "Startup" en Windows. Así, cada vez que se encienda la máquina, Roberto te volverá a mandar la señal automáticamente.

### Puntos aparte
**¿Cómo podemos defendernos, como informáticos(as), ante un Backdoor con la técnica de ReverseShell?**

* **Filtrado de Salida (Egress Filtering):** Configurar el firewall o Router para que bloquee todas las conexiones salientes por defecto, excepto las que son estrictamente necesarias (como el puerto 80 para HTTP o 443 para HTTPS).
* **Saber auditar lo que esta pasando en caliente:** Con comandos como `netstat -antp` o `ss -tp` en Linux, y buscando conexiones en estado ESTABLISHED hacia IPs externas desconocidas.
* **Implementar antivirus de próxima generación:** Soluciones de seguridad basadas en la nube que utilizan IA + Machine Learning, y estos están más basados en el analisis de los comportamientos, y no tanto en las extensiones de los archivos (como .exe) de los tradicionales para detectar amenazas en tiempo real.
* **Prevención (Bastionado / Hardening de Sistemas):** Si el server Ubuntu no necesita python como función principal se puede desinstalar, ya que sin el intérprete de Python, un ataque de "ReverseShell con Python" como el que hice simplemente no funcionará porque la máquina no entenderá el código.
* **Principio de Menor Privilegio:** Si la victima es un usuario limitado sin acceso a root, será como quedar "atrapado" en una jaula pequeña, si instala persistencia será limitada y no podrá leer archivos externos.

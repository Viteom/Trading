# Despliegue permanente: VPS Linux con systemd

Requiere un servidor encendido permanentemente, Python >=3.12, systemd y acceso HTTPS a www.okx.com y api.telegram.org. No instalar en una región bloqueada por el proveedor. No contratar servicios sin aprobación del usuario. Un único agente debe enviar al grupo: detener la instancia de Codex antes de habilitar producción.

1. Copiar este proyecto a `/opt/trading-agent`, sin `.git`, `__pycache__` ni credenciales. Transferir aparte la base `.local/paper-okx-4h.db` con el agente detenido si se desea conservar el estado; no sobrescribir una base existente.
2. Como administrador, crear usuario de sistema y permisos:

```sh
sudo useradd --system --home /opt/trading-agent --shell /usr/sbin/nologin trading-agent
sudo install -d -o trading-agent -g trading-agent -m 700 /opt/trading-agent/.local
sudo chown -R trading-agent:trading-agent /opt/trading-agent/.local
sudo install -m 600 /opt/trading-agent/deploy/trading-agent.env.example /etc/trading-agent.env
sudoedit /etc/trading-agent.env
```

Introducir el token original de BotFather en ese archivo, sin compartirlo por chat ni copiar un placeholder del proxy de Codex. Verificar el chat de destino. Los secretos de Codex no se transfieren automáticamente al VPS. El código debe ser legible por el usuario del servicio.

3. Validar y activar:

```sh
cd /opt/trading-agent
python3 -m unittest discover -s tests -v
sudo install -m 644 deploy/trading-agent.service /etc/systemd/system/trading-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now trading-agent
sudo systemctl status trading-agent
curl --fail http://127.0.0.1:8000/api/state
```

Exigir `status=ok`, `timeframe=4H`, `telegram=configured` o `sent`, y dos mercados con datos recientes. Telegram `configured` solo confirma presencia de configuración, no entrega. Verificar entrega real al grupo antes de declarar notificaciones listas.

4. Verificar reinicio con `sudo systemctl restart trading-agent`, volver a comprobar estado y persistencia. `systemctl is-enabled trading-agent` debe indicar enabled. Los fallos del proceso provocan reinicio; si el ciclo de análisis se bloquea más de 180 segundos, el watchdog lo reinicia. Los errores de red se muestran como degraded y se reintentan cada ciclo; no reiniciar ciegamente ante una restricción regional.

El panel escucha solo en loopback: acceder por túnel SSH si se necesita, sin exponerlo públicamente. Este servicio no asegura disponibilidad absoluta: el VPS puede fallar. Usar monitorización externa y copias de la base para operación sostenida. No hay garantía de entrega exactamente una vez; un timeout o caída tras un envío puede producir un duplicado. No envía órdenes reales. Las señales dependen de la estrategia, no se generan obligatoriamente cada cuatro horas.

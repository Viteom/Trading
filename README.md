# Trading Agent — prototipo de futuros en simulación

Python 3.12+, sin dependencias externas. Ejecutar desde `/workspace/Trading`:

```sh
python -m unittest discover -s tests -v
python server.py
```

El servidor escucha en 127.0.0.1:8000. `GET /api/state` expone estado, señales y operaciones; `/` sirve el panel. Requiere HTTPS a `www.okx.com`. No requiere claves ni tiene capacidad de enviar órdenes. Si la red falla, muestra estado `degraded`; nunca sustituye cotizaciones por datos ficticios.

Cada 30 segundos consulta BTCUSDT y ETHUSDT, con velas de 4 horas. Descarta la vela abierta. Señales por cruce EMA20/50 con filtro RSI simple de 14 periodos. Una señal por vela; una posición global; capital inicial 100 USDT. Tamaño con riesgo teórico 0,5%, margen máximo 25% y apalancamiento fijo 5x. Stop a 2 ATR (mínimo 0,3%); objetivo bruto de 5% sobre el margen de cada operación: movimiento favorable de precio de 1% a 5x. Las comisiones reducen el rendimiento neto; no es un objetivo diario. El stop depende del ATR, por lo que la relación beneficio/riesgo varía. Las posiciones ya abiertas conservan su objetivo original. Pausa entradas tras pérdida realizada diaria del 2%, con día UTC. Base SQLite en `.local/paper-okx-4h.db` (bases anteriores conservadas).

Simulación experimental: entradas y salidas al precio observado, comisión y deslizamiento combinados estimados de 0,06% por lado. El panel muestra patrimonio realizado, no valoración de posiciones abiertas. No modela funding, liquidaciones, filtros de cantidad de Binance ni movimientos entre consultas; gaps pueden superar el riesgo previsto. Los stops solo se evalúan mientras el agente funciona y obtiene datos. No hay backtest ni evidencia de rentabilidad. El usuario busca 5–10% por operación; el prototipo usa el extremo de 5% bruto sobre margen como hipótesis sin validar, sin prometer resultados.

Las alertas aparecen en el panel y se envían a Telegram cuando está configurado. No integra TradingView ni ejecución real. Antes de operar dinero real hacen falta validación histórica fuera de muestra, pruebas en testnet, reglas de ejecución/reconciliación y límites acordados con el usuario. No introducir claves en chat ni en el repositorio.

## Fuente de mercado
El agente usa los perpetuos BTC-USDT-SWAP y ETH-USDT-SWAP de OKX, sin cuenta ni claves. Verifica precios recientes, velas confirmadas y continuidad del historial. Los precios y señales pueden diferir de Binance. La conectividad OKX fue validada en Codex; verificarla de nuevo en cada servidor.

## Telegram privado (opcional)
Crear un grupo privado y un bot con @BotFather, añadir únicamente el bot al grupo y desactivar permisos para que miembros inviten personas. No existe un usuario humano del agente que se pueda invitar. Los grupos normales de Telegram no tienen cifrado de extremo a extremo. Configurar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en el proceso mediante un gestor seguro; nunca guardar el token en Git o compartirlo por chat. El envío está desactivado si falta cualquiera. Necesita HTTPS a api.telegram.org. Las alertas corresponden a entradas simuladas aceptadas, no a toda señal candidata; sin configuración, solo aparecen en el panel. Se confirmó una entrega de prueba al grupo configurado desde Codex; cada despliegue requiere validación propia.

## Operación 24/7
Ver [deploy/README.md](deploy/README.md) para servicio systemd con arranque automático, reinicio y watchdog. El despliegue permanente todavía no se ha realizado: Codex no es un servidor 24/7.

## Uso manual en Windows
Ver windows/LEEME.txt y ejecutar windows/iniciar.ps1 en PowerShell. Las alertas solo funcionan con el programa abierto y el computador conectado y sin suspensión. La instancia de Codex se detuvo para evitar envíos fuera de estas sesiones. El lanzador solicita el token de forma oculta y no lo guarda. No se ha validado el lanzador en Windows.

## Consultas por Telegram
Con el programa abierto, en el grupo configurado: `/analizar BTC`, `/analizar ETH`, `/analizar SOL` o `/analizar SOLUSDT`. También se puede mencionar al bot: `/analizar@UsuarioDelBot SOL`. `/ayuda` muestra instrucciones.

Usa velas cerradas de 4 horas y las mismas reglas EMA20/50 + RSI. Devuelve LONG, SHORT o ESPERAR y los indicadores. Solo propone stop y objetivo cuando hay señal. No es un modelo de lenguaje ni interpreta texto libre, noticias, imágenes, posiciones actuales o el contexto de una operación. La consulta no abre una operación simulada, no cambia el saldo y no amplía el seguimiento automático de BTC/ETH. Requiere un perpetuo USDT listado en OKX con historial suficiente; un mercado no disponible produce un aviso, sin inventar datos.

Solo responde al grupo TELEGRAM_CHAT_ID configurado. Acepta órdenes de cualquier miembro de ese grupo; mantenerlo privado. Descarta mensajes de más de dos minutos para no ejecutar consultas antiguas tras un apagado. Guarda el cursor de Telegram en `.local/telegram-updates.db` antes de responder: si el proceso falla o el envío se pierde, puede ser necesario repetir el comando. Ejecutar una sola instancia por bot; otro consumidor de getUpdates o un webhook puede impedir recibir comandos. El programa hace polling; no requiere puertos públicos. El envío de prueba previo validó Telegram, pero las consultas nuevas requieren una prueba completa en el Windows del usuario.

# Trading Agent — futuros en simulación

Python 3.12+, sin dependencias externas. Ejecutar desde la carpeta del proyecto:

```sh
python -m unittest discover -s tests -v
python server.py
```

El servidor escucha solo en 127.0.0.1:8000. `/api/state` muestra datos, señales, estado Telegram y operaciones. `/` sirve el panel. Requiere HTTPS a www.okx.com y, para Telegram, api.telegram.org. No tiene capacidad para enviar órdenes reales.

## Estrategia v2 — velas cerradas de 4 horas

Fuente: perpetuos USDT de OKX. Seguimiento automático de BTC/ETH; consultas por símbolo para otros perpetuos con suficiente historial. Se solicitan hasta 300 velas para inicializar indicadores (mínimo 100 cerradas). El resultado puede variar respecto a TradingView por historial, fuente y fórmulas.

- EMAs 10, 55 y 100, inicializadas con el primer cierre disponible.
- RSI14 con suavizado de Wilder. LONG exige 50 < RSI < 70; SHORT, 30 < RSI < 50.
- ADX14 con suavizado de Wilder, umbral >=20. LONG exige +DI > -DI; SHORT, -DI > +DI.
- Squeeze inspirado en LazyBear: Bollinger 20, desviación poblacional ×2; Keltner 20, SMA del true range ×1,5. Compresión ON si BB está dentro de KC; OFF si está fuera. Momentum: regresión lineal de 20 periodos del cierre menos el promedio entre el punto medio de máximos/mínimos de 20 periodos y la SMA20. Se usa el extremo final de la recta.
- LONG: cierre > EMA10 > EMA55 > EMA100, RSI y ADX/DI válidos, squeeze OFF, momentum positivo y creciente.
- SHORT: cierre < EMA10 < EMA55 < EMA100, RSI y ADX/DI válidos, squeeze OFF, momentum negativo y decreciente.
- Solo hay señal al pasar de NO cumplir a cumplir TODA la configuración entre las dos últimas velas cerradas. Si ya se cumplía antes, responde ESPERAR para no repetir la entrada. No exige que el squeeze se haya liberado justo en esa vela.

Referencia conceptual: https://www.tradingview.com/script/nqQ1DT5a-Squeeze-Momentum-Indicator-LazyBear/ . El acceso a esa página fue bloqueado por el proxy; no se inspeccionó el código exacto. Esta implementación NO está verificada como equivalente al script de LazyBear. Algunas variantes históricas emplean distintos multiplicadores o parámetros. No se ha validado rentabilidad ni comparado valores uno a uno con TradingView.

No analiza noticias, datos fundamentales, volumen, interés abierto, financiación, soportes/resistencias ni posiciones del usuario. No es un modelo de lenguaje. Requiere evaluación histórica fuera de muestra antes de considerar dinero real.

## Frecuencia y gestión de riesgo

El ciclo consulta precio de marca cada 30 segundos para vigilar stops/objetivos simulados. Conserva velas en memoria hasta el siguiente cierre de 4 horas y recalcula el análisis automático solo cuando cambia la vela cerrada. Las consultas manuales recalculan los indicadores sobre el mismo historial confirmado. Tras un reinicio, recarga datos. Un cierre retrasado se vuelve a consultar, sin inventar cotizaciones.

Capital inicial simulado 100 USDT, apalancamiento fijo 5x, riesgo teórico 0,5% del capital por operación incluyendo costes estimados, margen máximo 25%. Stop a 2 ATR14 Wilder (mínimo 0,3% del precio). Objetivo bruto 5% sobre margen: movimiento favorable del precio de 1% a 5x. El 10% no está implementado. El objetivo/stop varía con la volatilidad y puede ser inferior a 1; se muestra en consultas. Una posición global y pausa de entradas tras perder 2% diario realizado (día UTC).

Base `.local/paper-okx-4h.db`. La actualización conserva saldo, posiciones, niveles y señales ya registrados; no migra ni borra históricos. Las bases anteriores siguen intactas. Una posición anterior mantiene su stop y objetivo.

Comisión y deslizamiento combinados estimados de 0,06% por lado. No modela funding, liquidaciones, filtros de cantidad ni movimientos entre consultas. Gaps pueden superar el riesgo previsto. El patrimonio mostrado es realizado. Cuando el programa está apagado no vigila posiciones ni reconstruye movimientos perdidos: las órdenes de protección de operaciones reales deben colocarse en Binance directamente.

## Consultas privadas por Telegram

Configurar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID de forma segura; no compartir tokens ni guardarlos en Git. El programa solo responde al grupo configurado, a cualquiera de sus miembros. Una única instancia por bot. No configurar un webhook simultáneo al polling.

Comandos: `SOL`, `BTC`, `ETH`, `SOLUSDT`, Bitcoin, Ethereum, Solana; también `/analizar SOL` y `/analizar@UsuarioDelBot SOL`; `/ayuda` muestra instrucciones. Para recibir símbolos sin comando: @BotFather → `/setprivacy` → seleccionar el bot → Disable; quitar y volver a añadir el bot al grupo. Mantenerlo solo en el grupo privado: desactivar privacidad permite que reciba mensajes normales en grupos.

Las consultas NO abren posiciones ni añaden mercados a la vigilancia automática. LONG/SHORT/ESPERAR son resultados de reglas, no garantías. Se rechazan consultas de más de dos minutos. El cursor se guarda antes de responder en `.local/telegram-updates.db`; si falla el envío, repetir el comando. Un envío automático con timeout puede duplicarse al reintentar.

En Codex se validaron datos reales de OKX y una entrega previa de prueba a Telegram. La estrategia v2 requiere actualización y comprobación en el PC; su recepción por Telegram no se ha probado allí todavía.

## Uso en Windows

Ver windows/LEEME.txt y ejecutar windows/iniciar.ps1. Introducir el grupo y el token oculto al iniciar. El lanzador no guarda el token. Funciona mientras el programa esté abierto y el computador tenga Internet y no esté suspendido. No detecta presencia. La instancia de Codex está detenida deliberadamente; no iniciarla para envíos paralelos.

## Operación permanente opcional

Ver deploy/README.md para systemd con reinicio y watchdog. No se ha instalado en un VPS. La opción actual elegida por el usuario es ejecución manual en su PC.

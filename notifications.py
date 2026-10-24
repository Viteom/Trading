"""Optional Telegram notifications; credentials must never enter logs."""
import json
import os
import urllib.parse
import urllib.request


def configured():
    return bool(os.environ.get('TELEGRAM_BOT_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'))


def message(trade):
    return (f"SIMULACIÓN · OKX · 4 horas\n{trade['symbol']} {trade['side']}\n"
            f"Referencia: {trade['entry']:.4f}\nStop: {trade['stop']:.4f}\nObjetivo: {trade['target']:.4f}\n"
            "5x · Objetivo bruto 5% sobre margen por operación; neto menor por costes.\n"
            "Capital inicial simulado: 100 USDT. Riesgo teórico 0,5% del capital.\n"
            "Cruce EMA20/50 + RSI. No garantiza ganancias. Precio Binance puede diferir.")


def send(trade):
    if not configured():
        return 'disabled'
    payload=urllib.parse.urlencode({'chat_id':os.environ['TELEGRAM_CHAT_ID'], 'text':message(trade), 'protect_content':'true'}).encode()
    # Never propagate an exception containing the token-bearing request URL.
    try:
        request=urllib.request.Request('https://api.telegram.org/bot'+os.environ['TELEGRAM_BOT_TOKEN']+'/sendMessage',data=payload)
        with urllib.request.urlopen(request,timeout=10) as response:
            result=json.load(response)
        return 'sent' if result.get('ok') else 'failed'
    except Exception:
        return 'failed'

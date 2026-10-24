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
            "EMA10/55/100 + RSI14 + ADX14 + Squeeze inspirado en LazyBear. No garantiza ganancias. Precio Binance puede diferir.")


def api(method, parameters, timeout=15):
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        return None
    try:
        payload=urllib.parse.urlencode(parameters).encode()
        request=urllib.request.Request('https://api.telegram.org/bot'+os.environ['TELEGRAM_BOT_TOKEN']+'/'+method,data=payload)
        with urllib.request.urlopen(request,timeout=timeout) as response:
            result=json.load(response)
        return result if result.get('ok') else None
    except Exception:
        # Telegram URLs contain credentials: never propagate or log exceptions.
        return None


def send_text(text):
    if not configured():
        return 'disabled'
    return 'sent' if api('sendMessage',{'chat_id':os.environ['TELEGRAM_CHAT_ID'], 'text':text, 'protect_content':'true'}) else 'failed'


def send(trade):
    return send_text(message(trade))

"""Deterministic analysis commands; isolated from the paper trading account."""
import os
import re
import sqlite3
import time
from pathlib import Path
from bot import analyze, position_size
from feed import fetch
from notifications import api, send_text


def answer(text):
    parts=text.strip().split()
    if not parts:
        return None
    command=parts[0].split('@')[0].lower()
    if command in ('/ayuda','/start'):
        return ('Escribe BTC, ETH, SOL o /analizar SOL.\n'
                'Solo análisis técnico por reglas con velas cerradas de 4 horas de OKX. '
                'No abre operaciones ni modifica la simulación. Puede responder ESPERAR. '
                'Funciona mientras el programa esté abierto.')
    if command=='/analizar':
        if len(parts)!=2:
            return 'Escribe SOL o usa /analizar SOL.'
        symbol=parts[1].upper()
    elif len(parts)==1 and re.fullmatch(r'[A-Za-z0-9]{1,24}',parts[0]):
        symbol=parts[0].upper()
    else:
        return None
    symbol={'BITCOIN':'BTC','ETHEREUM':'ETH','SOLANA':'SOL'}.get(symbol,symbol)
    if not symbol.endswith('USDT'):
        symbol+='USDT'
    if not re.fullmatch(r'[A-Z0-9]{1,20}USDT',symbol):
        return 'Símbolo inválido. Ejemplo: /analizar SOL'
    try:
        rows,mark=fetch(symbol)
        signal=analyze(rows)
    except Exception:
        return ('No pude analizar ese futuro USDT de OKX: mercado no disponible, '
                'historial insuficiente o error de datos/conexión. No hay recomendación de entrada.')
    verdict={'WAIT':'ESPERAR','LONG':'LONG','SHORT':'SHORT'}[signal['side']]
    result=(f'CONSULTA · {symbol} · OKX · 4H\nResultado por reglas: {verdict}\n'
            f'Precio de marca: {mark:.6g}\nRSI: {signal["rsi"]} · '
            f'EMA20: {signal["ema20"]:.6g} · EMA50: {signal["ema50"]:.6g}\n'
            f'{signal["reason"]}\n')
    if signal['side']!='WAIT':
        _,distance=position_size(100,mark,signal['atr'])
        direction=1 if signal['side']=='LONG' else -1
        result+=(f'Stop de referencia: {mark-direction*distance:.6g}\n'
                 f'Objetivo: {mark*(1+direction*.05/5):.6g}\n'
                 f'Relación objetivo/stop antes de costes: {mark*.01/distance:.2f}\n'
                 'Objetivo bruto 5% sobre margen a 5x; comisiones reducen el neto.\n')
    else:
        result+='No hay señal de entrada válida según esta estrategia.\n'
    return result+('Consulta informativa: no abre posiciones ni evalúa tus posiciones actuales. '
                   'No garantiza ganancias. Contrasta precios y riesgo en Binance antes de decidir.')


def process_update(update):
    msg=update.get('message',{})
    chat=msg.get('chat',{})
    if str(chat.get('id'))!=os.environ.get('TELEGRAM_CHAT_ID') or chat.get('type') not in ('group','supergroup'):
        return None
    if time.time()-msg.get('date',0)>120 or msg.get('from',{}).get('is_bot'):
        return None
    # Accept only this bot's mention, avoiding commands addressed to other bots.
    text=msg.get('text','')
    token=text.split(maxsplit=1)[0] if text else ''
    if '@' in token and token.split('@',1)[1].lower()!=os.environ.get('TELEGRAM_BOT_USERNAME','').lower():
        return None
    reply=answer(text)
    return send_text(reply) if reply else None


def command_worker():
    me=api('getMe',{})
    if not me:
        print('Consultas Telegram: no se pudo verificar el bot; reinicia para reintentar.',flush=True)
        return
    os.environ['TELEGRAM_BOT_USERNAME']=me['result']['username']
    path=Path(__file__).parent/'.local'/'telegram-updates.db'
    path.parent.mkdir(exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS cursor(id INTEGER PRIMARY KEY, offset INTEGER)')
        db.execute('INSERT OR IGNORE INTO cursor VALUES(1,0)')
        db.commit()
        while True:
            offset=db.execute('SELECT offset FROM cursor WHERE id=1').fetchone()[0]
            updates=api('getUpdates',{'offset':offset,'timeout':20,'allowed_updates':'["message"]'},timeout=30)
            if not updates:
                print('Consultas Telegram: conexión no disponible; reintentando.',flush=True)
                time.sleep(10)
                continue
            for update in updates['result']:
                # Persist first to avoid resending replies after process restarts.
                with db:
                    db.execute('UPDATE cursor SET offset=? WHERE id=1',(update['update_id']+1,))
                process_update(update)

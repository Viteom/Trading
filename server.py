import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from bot import Agent, analyze
from feed import fetch
from notifications import configured, send
from commands import command_worker

snapshot = {'status':'starting','signals':[], 'mode':'PAPER', 'provider':'OKX', 'timeframe':'4H', 'telegram':'disabled', 'error':None}
lock = threading.Lock()


def notify_service(message):
    address = os.environ.get('NOTIFY_SOCKET')
    if not address:
        return
    if address.startswith('@'):
        address = '\0' + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.sendto(message.encode(), address)

def worker():
    agent = Agent(Path(__file__).parent / '.local' / 'paper-okx-4h.db')
    agent.db.execute('CREATE TABLE IF NOT EXISTS notified(trade_id INTEGER PRIMARY KEY)')
    agent.db.commit()
    notification_status = 'configured' if configured() else 'disabled'
    analysis_cache={}
    while True:
        signals, errors = [], []
        for symbol in ('BTCUSDT','ETHUSDT'):
            try:
                rows, mark = fetch(symbol)
                candle=int(rows[-2][0])
                cached=analysis_cache.get(symbol)
                if cached is None or cached['candle']!=candle:
                    analysis_cache[symbol]=analyze(rows)
                signal=analysis_cache[symbol]
                agent.step(symbol,signal,mark)
                signals.append(dict(symbol=symbol,mark=mark,**signal))
            except Exception as exc:
                errors.append(f'{symbol}: {type(exc).__name__}: {exc}')
        for trade in agent.state()['trades']:
            if trade['closed'] is None and not agent.db.execute('SELECT 1 FROM notified WHERE trade_id=?',(trade['id'],)).fetchone():
                notification_status = send(trade)
                if notification_status == 'sent':
                    with agent.db:
                        agent.db.execute('INSERT INTO notified VALUES(?)',(trade['id'],))
        with lock:
            snapshot.update(telegram=notification_status,status='ok' if not errors else 'degraded', signals=signals,error='; '.join(errors) or None,updated=time.time(),**agent.state())
        print(time.strftime('%Y-%m-%d %H:%M:%S'), 'OKX:', 'OK' if not errors else 'SIN DATOS', '| Telegram:', notification_status, '|', ', '.join(x['symbol']+': '+x['side'] for x in signals), flush=True)
        notify_service('READY=1\nWATCHDOG=1')
        time.sleep(30)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/state':
            with lock:
                body = json.dumps(snapshot,allow_nan=False).encode()
            mime = 'application/json'
        elif self.path == '/':
            body = (Path(__file__).parent/'static/index.html').read_bytes()
            mime = 'text/html; charset=utf-8'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    # Let the service manager restart the process if its worker dies.
    threading.excepthook = lambda args: os._exit(1)
    threading.Thread(target=worker,daemon=True).start()
    if configured():
        threading.Thread(target=command_worker,daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()

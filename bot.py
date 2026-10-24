"""Public Binance market analysis and isolated paper execution. No order API."""
import json
import math
import sqlite3
import time
import urllib.request
from pathlib import Path

DB = Path(__file__).parent / '.local' / 'paper.db'
BASE = 'https://fapi.binance.com'

def market(path):
    request = urllib.request.Request(BASE + path, headers={'User-Agent': 'TradingResearch/1.0'})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

def ema(values, period):
    result = values[0]
    for value in values[1:]:
        result += 2 / (period + 1) * (value - result)
    return result

def analyze(rows):
    # Binance's last candle is still forming; never trade on it.
    closed = rows[:-1]
    if len(closed) < 60:
        raise ValueError('Se necesitan al menos 60 velas cerradas')
    prices = [float(row[4]) for row in closed]
    changes = [b-a for a,b in zip(prices[-15:-1], prices[-14:])]
    gain = sum(max(x, 0) for x in changes) / 14
    loss = sum(max(-x, 0) for x in changes) / 14
    rsi = 100 - 100/(1+gain/loss) if loss else (100 if gain else 50)
    atr = sum(max(float(closed[i][2])-float(closed[i][3]), abs(float(closed[i][2])-prices[i-1]), abs(float(closed[i][3])-prices[i-1])) for i in range(len(closed)-14,len(closed))) / 14
    fast, slow = ema(prices, 20), ema(prices, 50)
    prior_fast, prior_slow = ema(prices[:-1], 20), ema(prices[:-1], 50)
    side = 'WAIT'
    if prior_fast <= prior_slow and fast > slow and 50 < rsi < 70:
        side = 'LONG'
    elif prior_fast >= prior_slow and fast < slow and 30 < rsi < 50:
        side = 'SHORT'
    return dict(side=side, price=prices[-1], atr=atr, rsi=round(rsi,2), ema20=fast, ema50=slow, candle=int(closed[-1][0]), reason='Cruce EMA20/EMA50 confirmado con filtro RSI' if side != 'WAIT' else 'Sin cruce confirmado con RSI válido')

def position_size(equity, price, atr, leverage=5):
    if not all(math.isfinite(x) and x > 0 for x in (equity,price,atr)) or leverage not in (5,10):
        raise ValueError('Parámetros de riesgo inválidos')
    # 0.5% equity risk, 25% equity margin cap, including estimated round-trip costs.
    distance = max(2*atr, price*.003)
    quantity = min(equity*.005/(distance+price*.0012), equity*.25*leverage/price)
    return quantity, distance

class Agent:
    def __init__(self, db=DB):
        db = Path(db)
        db.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''CREATE TABLE IF NOT EXISTS account(id INTEGER PRIMARY KEY, equity REAL, day TEXT, day_start REAL);
        INSERT OR IGNORE INTO account VALUES(1,100,'',100);
        CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY, symbol TEXT, side TEXT, entry REAL, qty REAL, stop REAL, target REAL, opened REAL, closed REAL, exit REAL, pnl REAL);
        CREATE TABLE IF NOT EXISTS signals(symbol TEXT, candle INTEGER, PRIMARY KEY(symbol,candle));''')
        self.db.commit()

    def step(self, symbol, signal, mark, now=None):
        now = now or time.time()
        if not math.isfinite(mark) or mark <= 0:
            raise ValueError('Precio inválido')
        today = time.strftime('%Y-%m-%d', time.gmtime(now))
        with self.db:
            account = self.db.execute('SELECT * FROM account').fetchone()
            if account['day'] != today:
                self.db.execute('UPDATE account SET day=?, day_start=equity', (today,))
            opened = self.db.execute('SELECT * FROM trades WHERE closed IS NULL').fetchone()
            if opened and opened['symbol'] == symbol:
                direction = 1 if opened['side']=='LONG' else -1
                if direction*(mark-opened['stop']) <= 0 or direction*(mark-opened['target']) >= 0:
                    pnl = direction*(mark-opened['entry'])*opened['qty'] - (mark+opened['entry'])*opened['qty']*.0006
                    self.db.execute('UPDATE trades SET closed=?,exit=?,pnl=? WHERE id=?',(now,mark,pnl,opened['id']))
                    self.db.execute('UPDATE account SET equity=equity+?',(pnl,))
                return
            if opened or signal['side'] == 'WAIT':
                return
            account = self.db.execute('SELECT * FROM account').fetchone()
            # Halt new positions at 2% realized daily loss. One position across all symbols.
            if account['equity'] <= account['day_start']*.98:
                return
            inserted = self.db.execute('INSERT OR IGNORE INTO signals VALUES(?,?)',(symbol,signal['candle']))
            if inserted.rowcount == 0:
                return
            qty, distance = position_size(account['equity'],mark,signal['atr'])
            direction = 1 if signal['side']=='LONG' else -1
            self.db.execute('INSERT INTO trades(symbol,side,entry,qty,stop,target,opened) VALUES(?,?,?,?,?,?,?)',(symbol,signal['side'],mark,qty,mark-direction*distance,mark*(1+direction*.05/5),now))

    def state(self):
        return dict(account=dict(self.db.execute('SELECT * FROM account').fetchone()), trades=[dict(r) for r in self.db.execute('SELECT * FROM trades ORDER BY id DESC LIMIT 100')])

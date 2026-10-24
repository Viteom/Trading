"""OKX public perpetual futures feed. Does not access private account APIs."""
import json
import math
import time
import urllib.request

INTERVAL_MS = 4 * 60 * 60 * 1000

BASE = 'https://www.okx.com'

def request(path):
    req = urllib.request.Request(BASE+path, headers={'User-Agent':'TradingResearch/1.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        body=json.load(response)
    if body.get('code') != '0' or not body.get('data'):
        raise ValueError('OKX: respuesta sin datos válidos')
    return body['data']

def normalize(rows, now_ms):
    ordered=sorted(rows,key=lambda r:int(r[0]))
    if len(ordered)<61 or len({int(r[0]) for r in ordered}) != len(ordered):
        raise ValueError('Historial insuficiente o duplicado')
    for row in ordered:
        if len(row)<9 or any(not math.isfinite(float(v)) or float(v)<=0 for v in row[1:5]):
            raise ValueError('Vela inválida')
    # analyze() discards its last row; append a sentinel after confirmed bars.
    closed=[r for r in ordered if r[8]=='1']
    if len(closed)<60 or not 0 <= now_ms-(int(closed[-1][0])+INTERVAL_MS) <= INTERVAL_MS + 120000:
        raise ValueError('Velas cerradas insuficientes o desactualizadas')
    if any(int(b[0])-int(a[0])!=INTERVAL_MS for a,b in zip(closed,closed[1:])):
        raise ValueError('Historial con intervalos faltantes')
    return closed+[closed[-1]]

def fetch(symbol):
    inst={'BTCUSDT':'BTC-USDT-SWAP','ETHUSDT':'ETH-USDT-SWAP'}[symbol]
    rows=request(f'/api/v5/market/candles?instId={inst}&bar=4H&limit=150')
    marks=request(f'/api/v5/public/mark-price?instType=SWAP&instId={inst}')
    mark=marks[0]
    now=time.time()*1000
    if mark.get('instId')!=inst or abs(now-int(mark['ts']))>120000:
        raise ValueError('Precio de marca desactualizado o instrumento incorrecto')
    price=float(mark['markPx'])
    if not math.isfinite(price) or price<=0:
        raise ValueError('Precio de marca inválido')
    return normalize(rows,now),price

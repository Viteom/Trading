import unittest
from unittest.mock import patch
import feed

class CacheTests(unittest.TestCase):
    def test_closed_candles_reused_but_marks_refresh(self):
        rows=[[str(i*feed.INTERVAL_MS),'100','101','99','100','1','1','1','1'] for i in range(300)]
        clock=300*feed.INTERVAL_MS+1000
        calls=[]
        def request(path):
            calls.append(path)
            if '/candles?' in path: return [row[:] for row in rows]
            return [dict(instId='BTC-USDT-SWAP',ts=str(clock),markPx='100')]
        with patch.dict(feed._candle_cache,{},clear=True),patch('feed.time.time',return_value=clock/1000),patch('feed.request',side_effect=request):
            feed.fetch('BTCUSDT')
            feed.fetch('BTCUSDT')
            self.assertEqual(sum('/candles?' in p for p in calls),1)
            self.assertEqual(sum('/mark-price?' in p for p in calls),2)
            clock+=feed.INTERVAL_MS
            rows.append([str(300*feed.INTERVAL_MS),'100','101','99','100','1','1','1','1'])
            with patch('feed.time.time',return_value=clock/1000): feed.fetch('BTCUSDT')
            self.assertEqual(sum('/candles?' in p for p in calls),2)

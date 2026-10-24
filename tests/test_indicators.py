import unittest
from indicators import rma, linreg_last, snapshots, decide

class IndicatorTests(unittest.TestCase):
    def bullish(self):
        return dict(price=110,ema10=108,ema55=105,ema100=100,rsi=60,adx=25,
                    plus_di=30,minus_di=10,squeeze='OFF',momentum=2,previous_momentum=1)
    def test_wilder_smoothing(self):
        self.assertEqual(rma([1,2,3,4,5],3)[:3],[None,None,2])
        self.assertAlmostEqual(rma([1,2,3,4,5],3)[3],8/3)
    def test_linear_regression_endpoint(self):
        self.assertAlmostEqual(linreg_last([2+3*x for x in range(20)]),59)
    def test_flat_market_has_no_strength_or_momentum(self):
        rows=[[i,100,101,99,100,0] for i in range(200)]
        previous,current=snapshots(rows)
        self.assertEqual(current['rsi'],50)
        self.assertEqual(current['adx'],0)
        self.assertAlmostEqual(current['momentum'],0)
        self.assertEqual(current['squeeze'],'ON')
        self.assertEqual(decide(previous,current),'WAIT')
    def test_monotonic_market_direction_and_adx(self):
        rows=[[i,100+i,101+i,99+i,100+i,0] for i in range(200)]
        _,current=snapshots(rows)
        self.assertAlmostEqual(current['adx'],100)
        self.assertAlmostEqual(current['momentum'],9.5)
        self.assertAlmostEqual(current['atr'],2)
        self.assertEqual(current['rsi'],100)
        self.assertGreater(current['plus_di'],current['minus_di'])
        self.assertGreater(current['ema10'],current['ema55'])
        self.assertGreater(current['ema55'],current['ema100'])
    def test_new_long_and_each_filter_blocks_entry(self):
        current=self.bullish()
        previous=dict(current,adx=19)
        self.assertEqual(decide(previous,current),'LONG')
        self.assertEqual(decide(current,current),'WAIT')
        for field,value in [('adx',19),('squeeze','ON'),('rsi',75),('ema55',99),('minus_di',40),('momentum',-1)]:
            with self.subTest(field=field):
                self.assertEqual(decide(previous,dict(current,**{field:value})),'WAIT')
    def test_new_short(self):
        current=dict(price=90,ema10=92,ema55=95,ema100=100,rsi=40,adx=25,
                     plus_di=10,minus_di=30,squeeze='OFF',momentum=-2,previous_momentum=-1)
        self.assertEqual(decide(dict(current,adx=19),current),'SHORT')

import tempfile
import unittest
from pathlib import Path
from bot import Agent, analyze, position_size

class BotTests(unittest.TestCase):
    def test_size_caps_risk_and_margin(self):
        q,d = position_size(100,1000,10)
        self.assertLessEqual(q*(d+1000*.0012),.5)
        self.assertLessEqual(q*1000/5,25)
    def test_ignores_forming_candle(self):
        rows=[[i,100,101,99,100,0] for i in range(70)]
        a=analyze(rows)
        rows[-1][4]=1000000
        self.assertEqual(a,analyze(rows))
        self.assertEqual(a['side'],'WAIT')
    def test_stop_persistence_and_signal_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'db'
            agent=Agent(path)
            signal=dict(side='LONG',candle=1,atr=1)
            agent.step('BTCUSDT',signal,100)
            trade=agent.state()['trades'][0]
            self.assertAlmostEqual(trade['target'],101)
            agent.step('BTCUSDT',signal,trade['stop']-1)
            self.assertLess(agent.state()['account']['equity'],100)
            agent.step('BTCUSDT',signal,100)
            self.assertEqual(len(agent.state()['trades']),1)
            agent.db.close()
            self.assertEqual(len(Agent(path).state()['trades']),1)
    def test_single_position_and_daily_halt(self):
        with tempfile.TemporaryDirectory() as d:
            agent=Agent(Path(d)/'db')
            s=dict(side='SHORT',candle=1,atr=1)
            agent.step('BTCUSDT',s,100)
            agent.step('ETHUSDT',s,100)
            self.assertEqual(len(agent.state()['trades']),1)
            agent.step('BTCUSDT',s,110)
            agent.step('ETHUSDT',dict(s,candle=2),100)
            self.assertEqual(len(agent.state()['trades']),1)

if __name__ == '__main__': unittest.main()

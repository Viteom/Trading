import time
import unittest
from unittest.mock import patch
from commands import answer, process_update

class CommandTests(unittest.TestCase):
    def test_invalid_symbol_never_fetches(self):
        with patch('commands.fetch') as fetch:
            self.assertIn('inválido',answer('/analizar ../../test'))
            fetch.assert_not_called()
    def test_wait_does_not_offer_entry(self):
        s=dict(side='WAIT',rsi=50,ema20=100,ema50=100,reason='Sin cruce',atr=1)
        with patch('commands.fetch',return_value=([],100)),patch('commands.analyze',return_value=s):
            result=answer('/analizar SOL')
            self.assertIn('ESPERAR',result)
            self.assertNotIn('Stop de referencia',result)
    def test_short_levels(self):
        s=dict(side='SHORT',rsi=40,ema20=99,ema50=100,reason='Cruce',atr=1)
        with patch('commands.fetch',return_value=([],100)),patch('commands.analyze',return_value=s):
            result=answer('/analizar SOLUSDT')
            self.assertIn('Stop de referencia: 102',result)
            self.assertIn('Objetivo: 99',result)
    def test_only_configured_group_and_recent_messages(self):
        update={'message':{'chat':{'id':-123,'type':'group'},'date':time.time(),'text':'/analizar BTC'}}
        with patch.dict('os.environ',{'TELEGRAM_CHAT_ID':'-456'}),patch('commands.answer') as analyze:
            process_update(update)
            analyze.assert_not_called()
        update['message']['date']=0
        with patch.dict('os.environ',{'TELEGRAM_CHAT_ID':'-123'}),patch('commands.answer') as analyze:
            process_update(update)
            analyze.assert_not_called()
    def test_reply_in_group(self):
        update={'message':{'chat':{'id':-123,'type':'group'},'date':time.time(),'text':'/analizar BTC'}}
        with patch.dict('os.environ',{'TELEGRAM_CHAT_ID':'-123'}),patch('commands.answer',return_value='ESPERAR'),patch('commands.send_text',return_value='sent') as send:
            self.assertEqual(process_update(update),'sent')
            send.assert_called_once_with('ESPERAR')

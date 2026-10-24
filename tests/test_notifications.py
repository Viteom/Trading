import unittest
from unittest.mock import patch, MagicMock
from notifications import send

class NotificationTests(unittest.TestCase):
    def trade(self):
        return dict(symbol='BTCUSDT',side='LONG',entry=100.,stop=98.,target=101.)
    def test_disabled_without_credentials(self):
        with patch.dict('os.environ',{},clear=True), patch('urllib.request.urlopen') as request:
            self.assertEqual(send(self.trade()),'disabled')
            request.assert_not_called()
    def test_send_private_message(self):
        response=MagicMock()
        response.__enter__.return_value.read.return_value=b'{"ok":true}'
        with patch.dict('os.environ',{'TELEGRAM_BOT_TOKEN':'test','TELEGRAM_CHAT_ID':'-123'},clear=True), patch('urllib.request.urlopen',return_value=response) as request:
            self.assertEqual(send(self.trade()),'sent')
            self.assertIn(b'protect_content=true',request.call_args.args[0].data)

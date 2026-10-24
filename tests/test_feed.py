import unittest
from feed import normalize, INTERVAL_MS
from bot import analyze

class FeedTests(unittest.TestCase):
    def rows(self):
        return [[str(i*INTERVAL_MS),'100','101','99','100','1','1','1','1'] for i in range(125)]
    def test_reverse_order_and_open_bar(self):
        rows=self.rows()
        rows[-1][8]='0'
        rows[-1][4]='999'
        normalized=normalize(rows[::-1],124*INTERVAL_MS+1000)
        self.assertEqual(analyze(normalized)['candle'],123*INTERVAL_MS)
        self.assertEqual(analyze(normalized)['price'],100)
    def test_closed_bar_valid_until_next_bar_completes(self):
        rows=self.rows()
        rows[-1][8]='0'
        normalized=normalize(rows,124*INTERVAL_MS+850000)
        self.assertEqual(analyze(normalized)['candle'],123*INTERVAL_MS)

    def test_rejects_stale_and_gaps(self):
        rows=self.rows()
        with self.assertRaises(ValueError): normalize(rows,150*INTERVAL_MS)
        del rows[20]
        with self.assertRaises(ValueError): normalize(rows,125*INTERVAL_MS)

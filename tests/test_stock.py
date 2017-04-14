import unittest
from wallstreet import wallstreet
from tests.mockrequests import mockrequests


class StockTest(unittest.TestCase):
    def setUp(self):
        self.oldrequests = wallstreet.requests
        wallstreet.requests = mockrequests

    def test_price(self):
        s = wallstreet.Stock('GOOG')
        self.assertEqual(s.price, 834.34)

    def test_last_trade(self):
        s = wallstreet.Stock('GOOG')
        self.assertEqual(s.last_trade, '22 Mar 2017 11:38:12')

    def test_yahoo_price(self):
        s = wallstreet.Stock('GOOG', source='yahoo')
        self.assertEqual(s.price, 833.65)

    def test_yahoo_last_trade(self):
        s = wallstreet.Stock('GOOG', source='yahoo')
        self.assertEqual(s.last_trade, '22 Mar 2017 15:53:24')

    def tearDown(self):
        wallstreet.requests = self.oldrequests

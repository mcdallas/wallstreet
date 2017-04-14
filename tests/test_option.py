import unittest
from wallstreet import wallstreet, blackandscholes
from tests.mockrequests import mockrequests


class CallTest(unittest.TestCase):
    def setUp(self):
        self.oldrequests = wallstreet.requests
        wallstreet.requests = mockrequests
        blackandscholes.requests = mockrequests

    def test_creation(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017)

    def test_creation_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, source='yahoo')

    def test_closest_date(self):
        s = wallstreet.Call('GOOG', d=15, m=6, y=2017)
        self.assertEqual(s.expiration, '16-06-2017')

    def test_closest_strike(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=798)
        self.assertEqual(s.strike, 800)

    def test_strike(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017)
        s.set_strike(800)

    def test_strike_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, source='yahoo')
        s.set_strike(800)

    def test_price(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800)
        self.assertEqual(s.price, 40.39)

    def test_price_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800, source='yahoo')
        self.assertEqual(s.price, 40.39)

    def test_rate(self):
        self.assertEqual(wallstreet.Option.rate(0.2328767123287671), 0.007689726027397261)

    def test_bs_called_with(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017)
        s.T = 0.2328767123287671
        s.set_strike(800)
        self.assertEqual(s.BandS.K, 800)
        self.assertEqual(s.BandS.T, 0.2328767123287671)
        self.assertEqual(s.BandS.S, 834.34)
        self.assertEqual(s.BandS.opt_price, 40.39)
        self.assertEqual(s.BandS.r, 0.007689726027397261)

    def test_underlying_price(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800)
        self.assertEqual(s.underlying.price, 834.34)

    def test_underlying_price_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800, source='yahoo')
        self.assertEqual(s.underlying.price, 833.65)

    def tearDown(self):
        wallstreet.requests = self.oldrequests
        blackandscholes.requests = self.oldrequests

import unittest
from wallstreet import wallstreet, blackandscholes
from mockrequests import mockrequests


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

    def test_implied_volatility(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800)
        self.assertAlmostEqual(s.implied_volatility(), 0.10675562829797487)

    def test_implied_volatility_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800, source='yahoo')
        self.assertAlmostEqual(s.implied_volatility(), 0.11170413283822085)

    def test_delta(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800)
        self.assertAlmostEqual(s.delta(), 0.80957896307154442)

    def test_delta_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800, source='yahoo')
        self.assertAlmostEqual(s.delta(), 0.7951752675694479)

    def test_vega(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800)
        self.assertAlmostEqual(s.vega(), 1.0940845695074586)

    def test_vega_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800, source='yahoo')
        self.assertAlmostEqual(s.vega(), 1.1424473639351618)

    def test_underlying_price(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800)
        self.assertEqual(s.underlying.price, 834.34)

    def test_underlying_price_yahoo(self):
        s = wallstreet.Call('GOOG', d=16, m=6, y=2017, strike=800, source='yahoo')
        self.assertEqual(s.underlying.price, 833.65)

    def tearDown(self):
        wallstreet.requests = self.oldrequests
        blackandscholes.requests = self.oldrequests


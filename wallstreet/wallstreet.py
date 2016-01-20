import requests
import re, json
from dateutil import parser
from datetime import datetime, date
from wallstreet.constants import DATE_FORMAT, DATETIME_FORMAT
from wallstreet.blackandscholes import riskfree, BlackandScholes
from functools import wraps


def parse(val):
    if val == '-':
        return None
    if isinstance(val, str):
        val = val.replace(',', '')
    val = float(val)
    if val.is_integer():
        return int(val)
    return val

def strike_required(func):
    @wraps(func)
    def deco(self, *args, **kwargs):
        if self.strike:
            self.update()
            return func(self, *args, **kwargs)
        else:
            raise AttributeError('Use set_strike() method first')
    return deco

rate = riskfree()

class Stock:
    G_API = 'http://finance.google.com/finance/info?client=ig&q='

    def __init__(self, quote, exchange=None):
        quote = quote.upper()
        query = str(quote)
        if exchange: query = exchange.upper() + ":" + quote
        r = requests.get(__class__.G_API + query)

        jayson = r.text.replace('\n','')
        jayson = json.loads(jayson[2:])[0]

        try:
            self.ticker = jayson['t']
        except:
            self.ticker = None

        if r.status_code == 400 or self.ticker != quote:
            raise LookupError('Ticker symbol not found. Try adding the exchange parameter')

        self.id= jayson["id"]
        self.exchange = jayson['e']
        self._price = parse(jayson['l'])
        try:
            self.change = parse(jayson['c'])
            self.cp = parse(jayson['cp'])
        except ValueError:
            self.change = jayson['c']
            self.cp = jayson['cp']
        self._last_trade = parser.parse(jayson['lt_dts'])

    def update(self):
        self.__init__(self.ticker)

    def __repr__(self):
        return 'Stock(ticker=%s, price=%s)' % (self.ticker, self.price)

    @property
    def price(self):
        self.update()
        return self._price

    @property
    def last_trade(self):
        self.update()
        return self._last_trade.strftime(DATETIME_FORMAT)


class Option:
    G_API = 'https://www.google.com/finance/option_chain?q='

    def __init__(self,quote, d=date.today().day, m=date.today().month,
                 y=date.today().year):
        quote = quote.upper()
        query = str(quote)

        if d: query += '&expd=' + str(d)
        if m: query += '&expm=' + str(m)
        if y: query += '&expy=' + str(y)

        r = requests.get(__class__.G_API + query + '&output=json')
        if r.status_code == 400:
            raise LookupError('Ticker symbol not found.')

        valid_json = re.sub(r'(?<={|,)([a-zA-Z][a-zA-Z0-9_]*)(?=:)', r'"\1"', r.text)
        data = json.loads(valid_json)

        if 'expirations' not in data:
            raise LookupError('No options listed for this stock.')

        self._exp = [date(int(dic['y']), int(dic['m']), int(dic['d']))
                     for dic in data['expirations']]
        self.expiration = date(y,m,d)
        self.expirations = [exp.strftime(DATE_FORMAT) for exp in self._exp]
        self.underlying = Stock(quote)

        try:
            self.calls = data['calls']
            self.puts = data['puts']
        except KeyError:
            if all((d,m,y)) and 'loop' not in locals():
                closest_date = min(self._exp, key=lambda x: abs(x - self._expiration))
                print('No options listed for given date, using %s instead' % closest_date.strftime(DATE_FORMAT))
                loop = True
                self.__init__(quote, closest_date.day, closest_date.month, closest_date.year)
            else:
                raise ValueError('Possible expiration dates for this stock are:', self.expirations) from None

    @property
    def expiration(self):
        return self._expiration.strftime(DATE_FORMAT)

    @expiration.setter
    def expiration(self, val):
        self._expiration = val


class Call(Option):
    Option_type = 'Call'

    def __init__(self, quote, d=date.today().day, m=date.today().month,
                 y=date.today().year, strike=None, strict=False):
        quote = quote.upper()
        kw = {'d': d, 'm': m, 'y': y}
        super().__init__(quote, **kw)

        if self.__class__.Option_type == 'Call':
            self.data = self.calls
        elif self.__class__.Option_type == 'Put':
            self.data = self.puts

        self.ticker = quote
        self.strike = None
        self.strikes = tuple(parse(dic['strike']) for dic in self.data
                        if dic.get('p') != '-' )
        if strike:
            if strike in self.strikes:
                self.set_strike(strike)
            else:
                if strict:
                    raise LookupError('No options listed for given strike price.')
                else:
                    closest_strike = min(self.strikes, key=lambda x: abs(x - strike))
                    print('No option for given strike, using %s instead' % closest_strike)
                    self.set_strike(closest_strike)


    def set_strike(self, val):
        d = {}
        for dic in self.data:
            if parse(dic['strike']) == val and val in self.strikes:
                d = dic
                break
        if d:
            self._price = parse(d['p'])
            self.id = d['cid']
            self.exchange = d['e']
            self._bid = parse(d['b'])
            self._ask = parse(d['a'])
            self.strike = parse(d['strike'])
            self._change = parse(d.get('c', 0)) # change in currency
            self._cp = parse(d.get('cp', 0))  # percentage change
            self._volume = parse(d['vol'])
            self._open_interest = parse(d['oi'])
            self.code = d['s']
            self.T = (self._expiration - date.today()).days/365
            self.ticker = self.code[:-15]
            self.q = 0
            self.BandS = BlackandScholes(
                    self.underlying.price,
                    self.strike,
                    self.T,
                    self._price,
                    rate(self.T),
                    self.__class__.Option_type,
                    self.q
                    )

        else:
            raise LookupError('No options listed for given strike price.')

    def __repr__(self):
        if self.strike:
            return self.__class__.Option_type + "(ticker=%s, expiration=%s, strike=%s)" % (self.ticker, self.expiration, self.strike)
        else:
            return self.__class__.Option_type + "(ticker=%s, expiration=%s)" % (self.ticker, self.expiration)

    def update(self):
        self.__init__(self.ticker, self._expiration.day,
                     self._expiration.month, self._expiration.year,
                     self.strike)

    @property
    @strike_required
    def bid(self):
        return self._bid

    @property
    @strike_required
    def ask(self):
        return self._ask

    @property
    @strike_required
    def price(self):
        return self._price

    @property
    @strike_required
    def change(self):
        return self._change

    @property
    @strike_required
    def cp(self):
        return self._cp

    @property
    @strike_required
    def open_interest(self):
        return self._open_interest


    @strike_required
    def implied_volatility(self):
        return self.BandS.implied_volatility()

    @strike_required
    def delta(self):
        return self.BandS.delta()

    @strike_required
    def gamma(self):
        return self.BandS.gamma()

    @strike_required
    def vega(self):
        return self.BandS.vega()

    @strike_required
    def rho(self):
        return self.BandS.rho()

    @strike_required
    def theta(self):
        return self.BandS.theta()

class Put(Call):
    Option_type = 'Put'

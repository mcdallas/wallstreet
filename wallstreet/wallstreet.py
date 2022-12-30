import requests
import json

from datetime import datetime, date, timedelta
from time import mktime, sleep
from io import StringIO
from urllib.parse import urlencode

from wallstreet.constants import DATE_FORMAT, DATETIME_FORMAT
from wallstreet.blackandscholes import riskfree, BlackandScholes

from functools import wraps
from collections import defaultdict

def parse(val):
    if val == '-':
        return 0
    elif val is None:
        return None

    if isinstance(val, str):
        val = val.replace(',', '')
    val = float(val)
    if val.is_integer():
        return int(val)
    return val

# send headers=headers on every session.get request to add a user agent to the header per https://stackoverflow.com/questions/10606133/sending-user-agent-using-requests-library-in-python
def get_headers(agent='Mozilla/5.0'):
    headers = requests.utils.default_headers()
    headers.update(
        {
            'User-Agent': agent,
        }
    )
    
    return headers

class ClassPropertyDescriptor:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, objtype):
        return self.f.__get__(obj, objtype)()


def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


def strike_required(func):
    """ Decorator for methods that require the set_strike method to be used first """

    @wraps(func)
    def deco(self, *args, **kwargs):
        if self.strike:
            self.update()
            return func(self, *args, **kwargs)
        else:
            raise AttributeError('Use set_strike() method first')
    return deco


class YahooFinanceHistory:
    timeout = 5
    quote_link = 'https://query1.finance.yahoo.com/v7/finance/download/{quote}'

    def __init__(self, symbol, days_back=7, frequency='d'):
        self.symbol = symbol
        self.session = requests.Session()
        self.dt = timedelta(days=days_back)
        self.frequency = {'m': 'mo', 'w': 'wk', 'd': 'd'}[frequency]

    def get_quote(self):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError('This functionality requires pandas to be installed')

        now = datetime.utcnow()
        dateto = int(now.timestamp())
        datefrom = int((now - self.dt).timestamp())
        url = self.quote_link.format(quote=self.symbol)
        params = {'period1': datefrom, 'period2': dateto, 'interval': f'1{self.frequency}', 'events': 'history', 'includeAdjustedClose': True}
        headers = get_headers()
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text), parse_dates=['Date'])


class Stock:
    _G_API = 'http://finance.google.com/finance'
    _Y_API = 'https://query2.finance.yahoo.com/v7/finance/options/'

    def __init__(self, quote, exchange=None, source='yahoo'):
        quote = quote.upper()
        self._attempted_ticker = quote
        self._attempted_exchange = exchange

        self.source = source.lower()
        if self.source == 'google':
            self._google(quote, exchange)
        elif self.source == 'yahoo':
            self._yahoo(quote, exchange)

    def _yahoo(self, quote, exchange=None):
        """ Collects data from Yahoo Finance API """

        query = quote + "." + exchange.upper() if exchange else quote

        if not hasattr(self, '_session_y'):
            self._session_y = requests.Session()
        headers = get_headers()
        r = self._session_y.get(__class__._Y_API + query, headers=headers)

        if r.status_code == 404:
            raise LookupError('Ticker symbol not found.')
        else:
            r.raise_for_status()

        jayson = r.json()['optionChain']['result'][0]['quote']

        self.ticker = jayson['symbol']
        self._price = jayson['regularMarketPrice']
        self.currency = jayson['currency']
        self.exchange = jayson['exchange']
        self.change = jayson['regularMarketChange']
        self.cp = jayson['regularMarketChangePercent']
        self._last_trade = datetime.utcfromtimestamp(jayson['regularMarketTime'])
        self.name = jayson.get('longName', '')
        self.dy = jayson.get('trailingAnnualDividendYield', 0)

    def _google(self, quote, exchange=None):
        """ Collects data from Google Finance API """

        query = exchange.upper() + ":" + quote if exchange else quote

        params = {'output': 'json', 'q': query}

        if not hasattr(self, '_session_g'):
            self._session_g = requests.Session()
        headers = get_headers()
        r = self._session_g.get(__class__._G_API, params=params, headers=headers)

        try:
            jayson = r.text.replace('\n', '')
            jayson = json.loads(jayson[2:])[0]
            self.ticker = jayson['t']
        except:
            self.ticker = None

        if r.status_code == 400 or self.ticker != query.split(':')[-1]:
            raise LookupError('Ticker symbol not found. Try adding the exchange parameter')
        else:
            r.raise_for_status()

        self.id = jayson["id"]
        self.exchange = jayson['e']
        self._price = parse(jayson['l'])
        try:
            self.change = parse(jayson['c'])
            self.cp = parse(jayson['cp'])
        except ValueError:
            self.change = jayson['c']
            self.cp = jayson['cp']
        self._last_trade = None
        self.name = jayson['name']
        self.dy = parse(jayson.get('dy') or 0)/100

    def update(self):
        self.__init__(self._attempted_ticker, exchange=self._attempted_exchange, source=self.source)

    def __repr__(self):
        return 'Stock(ticker=%s, price=%s)' % (self.ticker, self.price)

    @property
    def price(self):
        self.update()
        return self._price

    @property
    def last_trade(self):
        if not self._last_trade:
            return None
        self.update()
        return self._last_trade.strftime(DATETIME_FORMAT)

    def historical(self, days_back=30, frequency='d'):
        return YahooFinanceHistory(symbol=self.ticker, days_back=days_back, frequency=frequency).get_quote()


class Option:
    _G_API = 'https://www.google.com/finance/option_chain'
    _Y_API = 'https://query2.finance.yahoo.com/v7/finance/options/'

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._has_run = False  # This is to prevent an infinite loop
        instance._skip_dates = defaultdict(set)  #  In case a date is listed as an expiration date but has only one type of options
        return instance

    def __init__(self, quote, opt_type, d=date.today().day, m=date.today().month,
                 y=date.today().year, strict=False, source='yahoo'):

        self.source = source.lower()
        self.underlying = Stock(quote, source=self.source)

        if self.source == 'google':
            self._google(quote, d, m, y)

        elif self.source == 'yahoo':
            self._yahoo(quote, d, m, y)

        self._exp = [exp for exp in self._exp if exp not in self._skip_dates[opt_type]]
        self.expirations = [exp.strftime(DATE_FORMAT) for exp in self._exp]
        self.expiration = date(y, m, d)

        try:
            if opt_type == 'Call':
                self.data = self.data['calls']
            elif opt_type == 'Put':
                self.data = self.data['puts']
            assert self.data

        except (KeyError, AssertionError):
            if self._expiration in self._exp:  # Date is in expirations list but no data for it
                self._skip_dates[opt_type].add(self._expiration)
                self._exp.remove(self._expiration)
                self._has_run = False

            if all((d, m, y)) and not self._has_run and not strict:
                closest_date = min(self._exp, key=lambda x: abs(x - self._expiration))
                print('No options listed for given date, using %s instead' % closest_date.strftime(DATE_FORMAT))
                self._has_run = True
                self.__init__(quote, closest_date.day, closest_date.month, closest_date.year, source=source)
            else:
                raise ValueError('Possible expiration dates for this option are:', self.expirations) from None

    def _yahoo(self, quote, d, m, y):
        """ Collects data from Yahoo Finance API """

        epoch = int(round(mktime(date(y, m, d).timetuple())/86400, 0)*86400)

        if not hasattr(self, '_session_y'):
            self._session_y = requests.Session()
        headers = get_headers()
        r = self._session_y.get(__class__._Y_API + quote + '?date=' + str(epoch), headers=headers)

        if r.status_code == 404:
            raise LookupError('Ticker symbol not found.')
        else:
            r.raise_for_status()

        json = r.json()

        try:
            self.data = json['optionChain']['result'][0]['options'][0]
        except IndexError:
            raise LookupError('No options listed for this stock.')

        self._exp = [datetime.utcfromtimestamp(i).date() for i in json['optionChain']['result'][0]['expirationDates']]

    def _google(self, quote, d, m, y):
        """ Collects data from Google Finance API """

        quote = quote.upper()
        query = str(quote)

        params = {'q': query}

        if d: params['expd'] = str(d)
        if m: params['expm'] = str(m)
        if y: params['expy'] = str(y)

        params['output'] = 'json'

        if not hasattr(self, '_session_g'):
            self._session_g = requests.Session()

        headers = get_headers()
        r = self._session_g.get(__class__._G_API, params=params, headers=headers)

        if r.status_code == 400:
            raise LookupError('Ticker symbol not found.')
        else:
            r.raise_for_status()

        valid_json = re.sub(r'(?<={|,)([a-zA-Z][a-zA-Z0-9_]*)(?=:)', r'"\1"', r.text)
        self.data = json.loads(valid_json)

        if 'expirations' not in self.data:
            raise LookupError('No options listed for this stock.')

        self._exp = [date(int(dic['y']), int(dic['m']), int(dic['d']))
                     for dic in self.data['expirations']]

    @classproperty
    def rate(cls):
        if not hasattr(cls, '_rate'):
            cls._rate = riskfree()

        return cls._rate

    @property
    def expiration(self):
        return self._expiration.strftime(DATE_FORMAT)

    @expiration.setter
    def expiration(self, val):
        self._expiration = val


class Call(Option):
    Option_type = 'Call'

    def __init__(self, quote, d=date.today().day, m=date.today().month,
                 y=date.today().year, strike=None, strict=False, source='yahoo'):

        quote = quote.upper()
        kw = {'d': d, 'm': m, 'y': y, 'strict': strict, 'source': source}
        super().__init__(quote, self.__class__.Option_type, **kw)

        self.T = (self._expiration - date.today()).days/365
        self.q = self.underlying.dy
        self.ticker = quote
        self.strike = None
        self.strikes = tuple(parse(dic['strike']) for dic in self.data
                             if dic.get('p') != '-')
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
        """ Specifies a strike price """

        d = {}
        for dic in self.data:
            if parse(dic['strike']) == val and val in self.strikes:
                d = dic
                break
        if d:
            self._price = parse(d.get('p')) or d.get('lastPrice')
            self.id = d.get('cid')
            self.exchange = d.get('e')
            self._bid = parse(d.get('b')) or d.get('bid', 0)
            self._ask = parse(d.get('a')) or d.get('ask', 0)
            self.strike = parse(d['strike'])
            self._change = parse(d.get('c')) or d.get('change', 0) # change in currency
            self._cp = parse(d.get('cp', 0)) or d.get('percentChange', 0) # percentage change
            self._volume = parse(d.get('vol')) or d.get('volume', 0)
            self._open_interest = parse(d.get('oi')) or d.get('openInterest', 0)
            self.code = d.get('s') or d.get('contractSymbol')
            self.itm = ((self.__class__.Option_type == 'Call' and self.underlying.price > self.strike) or
                (self.__class__.Option_type == 'Put' and self.underlying.price < self.strike)) # in the money
            self.BandS = BlackandScholes(
                    self.underlying.price,
                    self.strike,
                    self.T,
                    self._price,
                    self.rate(self.T),
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
                     self.strike, source=self.source)

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

    @property
    @strike_required
    def volume(self):
        return self._volume

    @strike_required
    def implied_volatility(self):
        return self.BandS.impvol

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

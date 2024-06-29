import requests
from yfinance.data import YfData

from datetime import datetime, date, timedelta
from time import mktime
from io import StringIO

from wallstreet.constants import DATE_FORMAT, DATETIME_FORMAT
from wallstreet.blackandscholes import riskfree, BlackandScholes

from functools import wraps
from collections import defaultdict

def parse(val):
    """
    This function takes a value (val) as input and attempts to parse it into a float.
    
    Parameters:
    val (str or float or int): The value to be parsed.
    
    Returns:
    float or int or None: The parsed value. If the input value is '-', it returns 0.
    If the input value is None, it returns None. If the input value is a string, it removes any commas
    and converts it into a float. If the resulting float is an integer, it returns that integer. Otherwise,
    it returns the float.
    """
    
    # Check if the input value is '-'
    if val == '-':
        # If it is, return 0
        return 0
    
    # Check if the input value is None
    elif val is None:
        # If it is, return None
        return None
    
    # Check if the input value is a string
    if isinstance(val, str):
        # If it is, remove any commas and convert it into a float
        val = val.replace(',', '')
        val = float(val)
    
    # Check if the resulting float is an integer
    if val.is_integer():
        # If it is, return the integer value
        return int(val)
    
    # Otherwise, return the float value
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
    """
    Decorator for class properties.

    This decorator is used to create a class property that can be accessed as if it
    were an instance attribute. The property is defined as a class method, which is
    then wrapped in a descriptor that allows it to be accessed as if it were an
    instance attribute.

    Args:
        func (function): The class method to be wrapped.

    Returns:
        ClassPropertyDescriptor: A descriptor that wraps the class method and allows
        it to be accessed as if it were an instance attribute.
    """

    # Check if the input function is already a classmethod or staticmethod. If not,
    # wrap it in a classmethod.
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    # Create a ClassPropertyDescriptor object and return it. The ClassPropertyDescriptor
    # object wraps the class method and allows it to be accessed as if it were an
    # instance attribute.
    return ClassPropertyDescriptor(func)


def strike_required(func):
    """ Decorator for methods that require the set_strike method to be used first """

    @wraps(func)  # This decorator preserves the name and docstring of the original function
    def deco(self, *args, **kwargs):  # This is the new function that will be used in place of the original function
        # Check if the strike attribute of the object is set
        if self.strike:
            # If the strike attribute is set, call the update method to update the object's attributes
            self.update()
            # Then call the original function with the object and any arguments passed to the new function
            return func(self, *args, **kwargs)
        else:  # If the strike attribute is not set
            # Raise an AttributeError with a message indicating that the set_strike method should be used first
            raise AttributeError('Use set_strike() method first')
    return deco


class YahooFinanceHistory:
    timeout = 5
    quote_link = 'https://query1.finance.yahoo.com/v7/finance/download/{quote}'

    def __init__(self, symbol, days_back=7, frequency='d'):
        """
        Initialize the YahooFinanceHistory object.

        Args:
            symbol (str): The ticker symbol of the stock.
            days_back (int, optional): The number of days of historical data to retrieve. Defaults to 7.
            frequency (str, optional): The frequency of the historical data. Can be 'd' for daily, 'w' for weekly, or 'm' for monthly. Defaults to 'd'.
        """
        # Set the ticker symbol of the stock
        self.symbol = symbol

        # Create a session object for making HTTP requests
        self.session = requests.Session()

        # Set the timeframe for the historical data. This is the time period that the data covers.
        # The number of days is calculated by subtracting the number of days back from the current date.
        # The frequency is determined by the value of the 'frequency' parameter. It can be 'd' for daily, 'w' for weekly, or 'm' for monthly.
        self.dt = timedelta(days=days_back)
        self.frequency = {
            'm': 'mo',  # Convert 'm' to 'mo' for monthly frequency
            'w': 'wk',  # Convert 'w' to 'wk' for weekly frequency
            'd': 'd'   # Use 'd' as is for daily frequency
        }[frequency]

    def get_quote(self):
        """
        Retrieve historical stock data from Yahoo Finance for the specified ticker symbol.

        This function uses the Yahoo Finance API to retrieve historical stock data for the specified ticker symbol.
        The data is retrieved in CSV format and is returned as a pandas DataFrame.

        Returns:
            pandas.DataFrame: A DataFrame containing the historical stock data.

        Raises:
            ImportError: If the pandas library is not installed.
            requests.exceptions.HTTPError: If the HTTP request to the Yahoo Finance API fails.
        """
        try:
            import pandas as pd  # Import the pandas library
        except ImportError:
            raise ImportError('This functionality requires pandas to be installed')  # Raise an ImportError if pandas is not installed

        now = datetime.utcnow()  # Get the current UTC datetime
        dateto = int(now.timestamp())  # Convert the current datetime to a Unix timestamp
        datefrom = int((now - self.dt).timestamp())  # Calculate the Unix timestamp for the specified number of days ago
        url = self.quote_link.format(quote=self.symbol)  # Construct the URL for the Yahoo Finance API
        params = {
            'period1': datefrom,  # Set the start date for the historical data
            'period2': dateto,  # Set the end date for the historical data
            'interval': f'1{self.frequency}',  # Set the interval for the historical data
            'events': 'history',  # Set the events parameter to retrieve historical data
            'includeAdjustedClose': True  # Set the includeAdjustedClose parameter to retrieve adjusted close data
        }
        headers = get_headers()  # Get the headers for the HTTP request
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)  # Send the HTTP request to the Yahoo Finance API
        response.raise_for_status()  # Raise an exception if the HTTP request fails
        return pd.read_csv(StringIO(response.text), parse_dates=['Date'])  # Read the CSV data from the response and return it as a pandas DataFrame


class Stock:
    _Y_API = 'https://query2.finance.yahoo.com/v7/finance/options/'

    def __init__(self, quote, exchange=None, source='yahoo'):
        """
        Initialize the Stock object.

        Args:
            quote (str): The ticker symbol of the stock.
            exchange (str, optional): The exchange where the stock is listed.
                Defaults to None.
            source (str, optional): The data source to use.
                Defaults to 'yahoo'.
        """

        # Convert the quote to uppercase for consistency.
        quote = quote.upper()

        # Store the original ticker symbol and exchange for later use.
        self._attempted_ticker = quote
        self._attempted_exchange = exchange

        # Create a requests session to reuse connections.
        self.session = requests.Session()

        # Initialize a YfData object with the session.
        self._yfdata = YfData(session=self.session)

        # Convert the source to lowercase for consistency.
        self.source = source.lower()

        # Call the _yahoo method to collect data from the Yahoo Finance API.
        self._yahoo(quote, exchange)

    def _yahoo(self, quote, exchange=None):
        """
        Method to collect data from the Yahoo Finance API.

        Args:
            quote (str): The ticker symbol of the stock.
            exchange (str, optional): The exchange where the stock is listed.
                Defaults to None.

        Raises:
            LookupError: If the ticker symbol is not found.

        Returns:
            None
        """

        # Construct the query string by appending the exchange to the quote symbol
        # if exchange is provided, otherwise use the quote symbol as it is
        query = f"{quote}.{exchange.upper()}" if exchange else quote

        # Construct the URL by appending the query to the Yahoo Finance API endpoint
        url = __class__._Y_API + query

        # Send a GET request to the Yahoo Finance API using the session object and the constructed URL
        r = self._yfdata.get(url)

        # Check if the response status code is 404 (not found)
        if r.status_code == 404:
            # If the ticker symbol is not found, raise a LookupError
            raise LookupError('Ticker symbol not found.')
        else:
            # If the response status code is not 404, raise an exception if the status code is not 200 (OK)
            r.raise_for_status()

        # Parse the JSON response and extract the quote information
        jayson = r.json()['optionChain']['result'][0]['quote']

        # Assign the extracted data to the corresponding instance variables
        self.ticker = jayson['symbol']  # The ticker symbol of the stock
        self._price = jayson['regularMarketPrice']  # The current price of the stock
        self.currency = jayson['currency']  # The currency in which the stock is traded
        self.exchange = jayson['exchange']  # The exchange where the stock is listed
        self.change = jayson['regularMarketChange']  # The change in the stock's price since the previous close
        self.cp = jayson['regularMarketChangePercent']  # The percentage change in the stock's price since the previous close
        self._last_trade = datetime.utcfromtimestamp(jayson['regularMarketTime'])  # The date and time of the last trade
        self.name = jayson.get('longName', '')  # The long name (company name) of the stock
        self.dy = jayson.get('trailingAnnualDividendYield', 0)  # The trailing annual dividend yield of the stock

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
    _Y_API = 'https://query2.finance.yahoo.com/v7/finance/options/'

    def __new__(cls, *args, **kwargs):
        """
        The __new__ method is a special method in Python that is called when an instance of a class is created.
        It is responsible for creating the instance and returns it.

        In this case, we override the __new__ method of the Option class to add some additional functionality.

        The __new__ method is called before the __init__ method. It is used to create the instance of the class.

        We first call the __new__ method of the parent class (super().__new__(cls)) to create the instance.
        Then, we add two additional attributes to the instance:
            - _has_run: This is a boolean flag that is initially set to False.
                         It is used to prevent an infinite loop in the __init__ method.
            - _skip_dates: This is a defaultdict that is used to keep track of dates that have only one type of options.
                           It is a dictionary where the keys are the option types and the values are sets of dates.

        Finally, we return the instance.
        """
        instance = super().__new__(cls)
        instance._has_run = False  # Set the _has_run flag to False
        instance._skip_dates = defaultdict(set)  # Create an empty defaultdict to store dates with only one type of options
        return instance

    def __init__(self, quote, opt_type, d=date.today().day, m=date.today().month,
                 y=date.today().year, strict=False, source='yahoo'):

        """
        Initialize the Option class.

        Parameters:
        - quote: The ticker symbol of the underlying stock.
        - opt_type: The type of option (Call or Put).
        - d: The day of the month for the option expiration.
        - m: The month of the year for the option expiration.
        - y: The year of the option expiration.
        - strict: A boolean flag that determines the behavior when there is no data for a given date.
                  If True, it raises a ValueError with the possible expiration dates.
                  If False, it prints a message and uses the closest date.
        - source: The source of the data. Currently only Yahoo Finance API is supported.

        The __init__ method first sets the source and creates an instance of the Stock class for the underlying stock.
        It then calls the _yahoo method to collect data from the Yahoo Finance API.

        Next, it filters out the expiration dates that do not have data for the given option type.
        It stores the remaining expiration dates in the expirations attribute.
        The expiration date for the option is set to the date specified by the user.

        The data for the option is then retrieved based on the option type.
        If there is no data for the given option type, it checks if the expiration date is in the list of possible expiration dates.
        If it is, it adds the expiration date to the _skip_dates dictionary and removes it from the list of possible expiration dates.
        If the user has not specified all the parameters (i.e., d, m, y) and the _has_run flag is False, it prints a message and calls itself with the closest date.
        If the _has_run flag is False and the user has specified all the parameters, it raises a ValueError with the possible expiration dates.
        """

        self.source = source.lower()
        self.underlying = Stock(quote, source=self.source)

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
        """
        Collects data from Yahoo Finance API.

        This method retrieves data for a given stock and its options from the Yahoo Finance API.
        It takes the ticker symbol of the stock, the day, month, and year of the desired option expiration date.
        It then converts the date to an epoch time, constructs the URL for the API request, and sends the request.
        If the request is successful, it parses the JSON response and stores the data for the options in the `data` attribute.
        If the request is unsuccessful (e.g., the ticker symbol is not found), it raises a `LookupError` with an appropriate error message.
        """

        # Convert the desired date to an epoch time
        epoch = int(round(mktime(date(y, m, d).timetuple())/86400, 0)*86400)

        # Use the underlying stock's Yahoo Finance data object for the API request
        self._yfdata = self.underlying._yfdata
        
        # Construct the URL for the API request
        url = __class__._Y_API + quote + '?date=' + str(epoch)

        # Send the API request and check the status code
        r = self._yfdata.get(url)
        
        if r.status_code == 404:
            raise LookupError('Ticker symbol not found.')
        else:
            r.raise_for_status()

        # Parse the JSON response
        json = r.json()

        try:
            # Store the data for the options in the `data` attribute
            self.data = json['optionChain']['result'][0]['options'][0]
        except IndexError:
            raise LookupError('No options listed for this stock.')

        # Convert the expiration dates to datetime objects and extract the dates
        self._exp = [datetime.utcfromtimestamp(i).date() for i in json['optionChain']['result'][0]['expirationDates']]

    @classproperty
    def rate(cls):
        """
        Class property decorator that returns the risk-free interest rate.

        This class property decorator retrieves the risk-free interest rate from the
        `riskfree` function. It first checks if the risk-free rate has been cached
        in the class (i.e., if the `_rate` attribute exists). If it has, it returns
        the cached value. If it hasn't, it calls the `riskfree` function to retrieve
        the risk-free rate and stores it in the `_rate` attribute. Finally, it returns
        the risk-free rate.

        Returns:
            float: The risk-free interest rate.
        """

        # Check if the risk-free rate has been cached
        if not hasattr(cls, '_rate'):
            # If not, retrieve it from the riskfree function and store it
            cls._rate = riskfree()

        # Return the risk-free rate
        return cls._rate

    @property
    def expiration(self):
        """
        Property decorator that returns the expiration date of the option in the
        format 'dd-mm-yyyy'.

        This property decorator returns the expiration date of the option in the
        format 'dd-mm-yyyy'. It does this by accessing the `_expiration` attribute
        of the `Option` object and calling the `strftime` method on it, passing in
        the `DATE_FORMAT` constant as an argument.

        Returns:
            str: The expiration date of the option in the format 'dd-mm-yyyy'.
        """

        # Access the `_expiration` attribute of the `Option` object
        # and call the `strftime` method on it, passing in the `DATE_FORMAT`
        # constant as an argument. Return the result.
        return self._expiration.strftime(DATE_FORMAT)

    @expiration.setter
    def expiration(self, val):
        """
        Setter method for the `expiration` property.

        This setter method is used to set the value of the `expiration` property.
        It takes a `val` parameter, which represents the value to be set.

        Parameters:
            val (datetime.date): The value to be set for the `expiration` property.

        Returns:
            None
        """

        # Set the `_expiration` attribute of the `Option` object to the value
        # passed in the `val` parameter. This effectively sets the expiration
        # date of the option.
        self._expiration = val


class Call(Option):
    Option_type = 'Call'

    def __init__(self, quote, d=date.today().day, m=date.today().month,
                 y=date.today().year, strike=None, strict=False, source='yahoo'):
        """
        Initialize the Call class.

        This method initializes a new instance of the Call class.

        Args:
            quote (str): The ticker symbol of the underlying stock.
            d (int, optional): The day of the expiration date. Defaults to today's day.
            m (int, optional): The month of the expiration date. Defaults to today's month.
            y (int, optional): The year of the expiration date. Defaults to today's year.
            strike (float, optional): The strike price of the option. Defaults to None.
            strict (bool, optional): Whether to raise an error if no options are listed for
                the given strike price. Defaults to False.
            source (str, optional): The data source to use. Defaults to 'yahoo'.
        """

        # Convert the quote to uppercase to ensure consistency
        quote = quote.upper()

        # Create a dictionary of keyword arguments to pass to the superclass constructor
        kw = {'d': d, 'm': m, 'y': y, 'strict': strict, 'source': source}

        # Call the superclass constructor with the quote, option type, and keyword arguments
        super().__init__(quote, self.__class__.Option_type, **kw)

        # Calculate the time to expiration of the option in years
        self.T = (self._expiration - date.today()).days/365

        # Get the daily change in price of the underlying stock
        self.q = self.underlying.dy

        # Set the ticker symbol of the option
        self.ticker = quote

        # Set the strike price of the option to None initially
        self.strike = None

        # Get the list of strike prices for the option
        self.strikes = tuple(parse(dic['strike']) for dic in self.data
                             if dic.get('p') != '-')

        # If a strike price is provided
        if strike:
            # If the strike price is in the list of available strike prices
            if strike in self.strikes:
                # Set the strike price of the option
                self.set_strike(strike)
            else:
                # If strict is True, raise an error
                if strict:
                    raise LookupError('No options listed for given strike price.')
                # Otherwise, find the closest strike price to the provided strike price
                else:
                    closest_strike = min(self.strikes, key=lambda x: abs(x - strike))
                    # Print a message indicating that the closest strike price is being used
                    print('No option for given strike, using %s instead' % closest_strike)
                    # Set the strike price of the option to the closest strike price
                    self.set_strike(closest_strike)

    def set_strike(self, val):
        """
        Specifies a strike price and updates the instance variables based on the
        data provided by the API.

        Args:
            val (float): The strike price to set.

        Raises:
            LookupError: If no option is listed for the given strike price.
        """

        # Initialize an empty dictionary to store the data for the given strike price
        d = {}

        # Iterate over the data obtained from the API
        for dic in self.data:
            # Check if the strike price matches the given value and if it is a valid strike price
            if parse(dic['strike']) == val and val in self.strikes:
                # If a match is found, update the dictionary with the data
                d = dic
                break

        # If a matching strike price is found
        if d:
            # Update the instance variables with the data from the dictionary

            # Price
            self._price = parse(d.get('p')) or d.get('lastPrice')

            # ID
            self.id = d.get('cid')

            # Exchange
            self.exchange = d.get('e')

            # Bid
            self._bid = parse(d.get('b')) or d.get('bid', 0)

            # Ask
            self._ask = parse(d.get('a')) or d.get('ask', 0)

            # Strike
            self.strike = parse(d['strike'])

            # Change (in currency)
            self._change = parse(d.get('c')) or d.get('change', 0)

            # Percentage change
            self._cp = parse(d.get('cp', 0)) or d.get('percentChange', 0)

            # Volume
            self._volume = parse(d.get('vol')) or d.get('volume', 0)

            # Open interest
            self._open_interest = parse(d.get('oi')) or d.get('openInterest', 0)

            # Code
            self.code = d.get('s') or d.get('contractSymbol')

            # Check if the option is in the money
            self.itm = ((self.__class__.Option_type == 'Call' and self.underlying.price > self.strike) or
                (self.__class__.Option_type == 'Put' and self.underlying.price < self.strike))

            # Calculate the Black and Scholes values
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
            # If no matching strike price is found, raise an error
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

    # This property decorator is used to define a read-only property
    # We use it to define the 'bid' attribute of the Call class.
    # The @strike_required decorator is used to ensure that the
    # 'bid' attribute can only be accessed if a strike price has
    # been set. If no strike price has been set, a LookupError
    # will be raised.
    @property
    @strike_required
    def bid(self):
        # This method is called when the 'bid' attribute is accessed.
        # It returns the value of the '_bid' attribute (which stores the
        # bid price).
        # The 'bid' attribute is read-only and cannot be changed directly.
        # Instead, it can only be updated by calling the 'update' method.
        return self._bid

    # This property decorator is used to define a read-only property
    # We use it to define the 'ask' attribute of the Call class.
    # The @strike_required decorator is used to ensure that the
    # 'ask' attribute can only be accessed if a strike price has
    # been set. If no strike price has been set, a LookupError
    # will be raised.
    #
    # The 'ask' attribute is the price at which the option can be sold.
    # It is also read-only and cannot be changed directly.
    # Instead, it can only be updated by calling the 'update' method.
    @property
    @strike_required
    def ask(self):
        # This method is called when the 'ask' attribute is accessed.
        # It returns the value of the '_ask' attribute (which stores the
        # ask price).
        #
        # The 'ask' attribute is read-only and cannot be changed directly.
        # Instead, it can only be updated by calling the 'update' method.
        return self._ask

    # This property decorator is used to define a read-only property.
    # We use it to define the 'price' attribute of the Call class.
    # The @strike_required decorator is used to ensure that the
    # 'price' attribute can only be accessed if a strike price has
    # been set. If no strike price has been set, a LookupError
    # will be raised.
    #
    # The 'price' attribute is the price at which the option can be traded.
    # It is read-only and cannot be changed directly. Instead, it can only
    # be updated by calling the 'update' method.
    @property
    @strike_required
    def price(self):
        # This method is called when the 'price' attribute is accessed.
        # It returns the value of the '_price' attribute (which stores the
        # option's current price).
        #
        # The 'price' attribute is read-only and cannot be changed directly.
        # Instead, it can only be updated by calling the 'update' method.
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

import requests
import xml.etree.ElementTree as ET

from scipy.interpolate import interp1d
from numpy import sqrt, log, exp
from scipy.stats import norm
from scipy.optimize import fsolve

from wallstreet.constants import *

import xml.etree.ElementTree as ET

def riskfree():
    """
    Function to retrieve the current risk-free interest rate from the US Treasury
    website. If the request fails, it returns a lambda function that returns a
    default risk-free rate.

    Returns:
        A function that takes a float x and returns the risk-free interest rate
        for that x.
    """
    try:
        # Send a GET request to the US Treasury website
        # This request retrieves an XML file containing the most recent risk-free
        # interest rates.
        r = requests.get(TREASURY_URL)

        # Parse the XML response
        # Convert the XML response to an ElementTree object, which allows us to
        # navigate the XML structure.
        root = ET.fromstring(r.text)

        # Find the most recent interest rate data
        # Find all the G_BC_CAT elements in the XML, which represent different
        # time periods of interest rate data. Take the last one.
        days = root.findall('.//G_BC_CAT')
        last = days[-1]

        # Define a helper function to parse a node and convert it to a float
        # This function takes an XML node and returns the float value of that
        # node's text.
        def parse(node):
            return float(node.text)

        # Parse various nodes in the XML response and convert them to floats
        # Parse the different interest rate nodes in the XML response and convert
        # them to floats.
        m1 = parse(last.find('BC_1MONTH'))
        m2 = parse(last.find('BC_2MONTH'))
        m3 = parse(last.find('BC_3MONTH'))
        m6 = parse(last.find('BC_6MONTH'))
        y1 = parse(last.find('BC_1YEAR'))
        y2 = parse(last.find('BC_2YEAR'))
        y3 = parse(last.find('BC_3YEAR'))
        y5 = parse(last.find('BC_5YEAR'))
        y7 = parse(last.find('BC_7YEAR'))
        y10 = parse(last.find('BC_10YEAR'))
        y20 = parse(last.find('BC_20YEAR'))
        y30 = parse(last.find('BC_30YEAR'))

        # Define the years and their corresponding interest rates
        # Define the different time periods for which we have interest rate data
        # and the corresponding interest rates.
        years = (0, 1/12, 2/12, 3/12, 6/12, 12/12, 24/12, 36/12, 60/12, 84/12, 120/12, 240/12, 360/12)
        rates = (OVERNIGHT_RATE, m1/100, m2/100, m3/100, m6/100, y1/100, y2/100, y3/100, y5/100, y7/100, y10/100, y20/100, y30/100)

        # Use scipy's interp1d function to create an interpolating function that
        # takes a float x and returns the risk-free interest rate for that x.
        # This function allows us to interpolate between the different interest
        # rate values we have, to estimate the risk-free interest rate for any
        # given time period.
        return interp1d(years, rates)
    except Exception:
        # If the request fails, return a lambda function that returns a default
        # risk-free rate.
        # If the request to the US Treasury website fails, we return a lambda
        # function that always returns the fallback risk-free rate.
        return lambda x: FALLBACK_RISK_FREE_RATE

class BlackandScholes:
    """
    Class implementing the Black-Scholes model for option pricing.
    """

    def __init__(self, S, K, T, price, r, option, q=0):
        """
        Initialize the BlackandScholes class with stock price S, strike price K,
        time to maturity T, option price price, risk-free rate r, option type
        option, and dividend yield q.
        """
        self.S, self.K, self.T, self.option, self.q = S, K, T, option, q
        self.r = r
        self.opt_price = price
        self.impvol = self.implied_volatility()

    @staticmethod
    def _BlackScholesCall(S, K, T, sigma, r, q):
        """
        Calculate the price of a call option using the Black-Scholes model.
        """
        d1 = (log(S/K) + (r - q + (sigma**2)/2)*T)/(sigma*sqrt(T))
        d2 = d1 - sigma*sqrt(T)
        return S*exp(-q*T)*norm.cdf(d1) - K*exp(-r*T)*norm.cdf(d2)

    @staticmethod
    def _BlackScholesPut(S, K, T, sigma, r, q):
        """
        Calculate the price of a put option using the Black-Scholes model.
        """
        d1 = (log(S/K) + (r - q + (sigma**2)/2)*T)/(sigma*sqrt(T))
        d2 = d1 - sigma*sqrt(T)
        return  K*exp(-r*T)*norm.cdf(-d2) - S*exp(-q*T)*norm.cdf(-d1)

    def _fprime(self, sigma):
        """
        Calculate the derivative of the option price with respect to the
        implied volatility.

        This function calculates the derivative of the option price with respect to
        the implied volatility by using the Black-Scholes model. It does this by
        first calculating d1, which is a measure of the option's sensitivity to
        changes in the underlying asset's price. It then uses d1 to calculate the
        derivative of the option price with respect to the implied volatility.

        Args:
            sigma (float): The implied volatility of the underlying asset.

        Returns:
            float: The derivative of the option price with respect to the implied
                   volatility.
        """
        # Calculate log(S/K), which is a measure of the option's sensitivity to
        # changes in the underlying asset's price.
        logSoverK = log(self.S/self.K)
        # Calculate n12, which is a measure of the option's sensitivity to
        # changes in the risk free interest rate.
        n12 = ((self.r + sigma**2/2)*self.T)
        # Calculate numerd1, which is the sum of logSoverK and n12.
        numerd1 = logSoverK + n12
        # Calculate d1, which is the ratio of numerd1 to the product of sigma and
        # the square root of T.
        d1 = numerd1/(sigma*sqrt(self.T))
        # Calculate the derivative of the option price with respect to the implied
        # volatility by multiplying S, sqrt(T), the pdf of d1, and exp(-r*T).
        return self.S*sqrt(self.T)*norm.pdf(d1)*exp(-self.r*self.T)

    def BS(self, S, K, T, sigma, r, q):
        """
        Calculate the option price using the Black-Scholes model.

        This method takes in the stock price S, strike price K, time to maturity T,
        the risk-free interest rate r, the volatility of the underlying asset sigma,
        and the dividend yield q. It returns the price of the option using the
        Black-Scholes model, which is a financial model that predicts the price
        of an option based on the current state of the underlying asset.

        The Black-Scholes model uses the Call and Put option formulas to calculate
        the price of the option. If the option type is 'Call', the _BlackScholesCall
        method is called. If the option type is 'Put', the _BlackScholesPut method
        is called. The _BlackScholesCall and _BlackScholesPut methods use the
        Black-Scholes formulas to calculate the option price.

        Parameters:
            S (float): The stock price.
            K (float): The strike price.
            T (float): The time to maturity in years.
            sigma (float): The volatility of the underlying asset.
            r (float): The risk-free interest rate.
            q (float): The dividend yield.

        Returns:
            float: The price of the option.
        """
        # Check if the option type is 'Call'
        if self.option == 'Call':
            # Call the _BlackScholesCall method to calculate the price of the option
            return self._BlackScholesCall(S, K, T, sigma, r, q)
        # Check if the option type is 'Put'
        elif self.option == 'Put':
            # Call the _BlackScholesPut method to calculate the price of the option
            return self._BlackScholesPut(S, K, T, sigma, r, q)

    def implied_volatility(self):
        """
        Calculate the implied volatility of the option.
        
        This method uses the fsolve function from scipy.optimize to find the root of the
        function impvol, which is defined as the difference between the calculated option
        price and the current option price. The root is the implied volatility.
        
        The fsolve function iteratively adjusts the input (in this case, the implied volatility)
        to find the root of the function. The function _fprime is the derivative of the function
        impvol with respect to the implied volatility. 
        
        The tolerance for the root is set to IMPLIED_VOLATILITY_TOLERANCE, which is a constant
        defined in constants.py.
        """
        # Define the function we want to find the root of
        impvol = lambda x: self.BS(self.S, self.K, self.T, x, self.r, self.q) - self.opt_price
        
        # Find the root of the function using fsolve
        iv = fsolve(impvol, SOLVER_STARTING_VALUE, fprime=self._fprime, xtol=IMPLIED_VOLATILITY_TOLERANCE)
        
        # Return the root, which is the implied volatility
        return iv[0]

    def delta(self):
        """
        Calculate the delta of the option.

        The delta of an option represents the rate of change of the option's price
        with respect to the underlying stock's price. If the underlying stock price
        increases, the delta will be positive. If the underlying stock price decreases,
        the delta will be negative.

        This function calculates the delta of the option by taking the difference
        between the option price when the underlying stock price is increased by a
        small amount (h) and the option price when the underlying stock price is
        decreased by the same amount (h). The ratio of these two differences to (2*h)
        is the delta of the option.

        Args:
            self (BlackandScholes): An instance of the BlackandScholes class.

        Returns:
            float: The delta of the option.
        """
        # Define the small amount to change the underlying stock price by
        h = DELTA_DIFFERENTIAL
        # Calculate the option price when the underlying stock price is increased by h
        p1 = self.BS(self.S + h, self.K, self.T, self.impvol, self.r, self.q)
        # Calculate the option price when the underlying stock price is decreased by h
        p2 = self.BS(self.S - h, self.K, self.T, self.impvol, self.r, self.q)
        # Calculate the delta of the option by taking the difference between p1 and p2
        # and dividing it by (2*h).
        return (p1-p2)/(2*h)

    def gamma(self):
        """
        Calculate the gamma of the option.

        The gamma of an option represents the rate of change of the option's delta with
        respect to the underlying stock's price. If the underlying stock price increases,
        the gamma will be positive. If the underlying stock price decreases, the gamma
        will be negative. The gamma is a measure of the option's sensitivity to changes
        in the underlying stock price.

        This function calculates the gamma of the option by taking the difference
        between the option price when the underlying stock price is increased by a
        small amount (h) and the option price when it is decreased by the same amount
        (h). It then divides the difference by (h**2) to get the gamma of the option.

        Args:
            self (BlackandScholes): An instance of the BlackandScholes class.

        Returns:
            float: The gamma of the option.
        """
        # Define the small amount to change the underlying stock price by
        h = GAMMA_DIFFERENTIAL
        # Calculate the option price when the underlying stock price is increased by h
        p1 = self.BS(self.S + h, self.K, self.T, self.impvol, self.r, self.q)
        # Calculate the option price when the underlying stock price is the same
        p2 = self.BS(self.S, self.K, self.T, self.impvol, self.r, self.q)
        # Calculate the option price when the underlying stock price is decreased by h
        p3 = self.BS(self.S - h, self.K, self.T, self.impvol, self.r, self.q)
        # Calculate the gamma of the option by taking the difference between p1 and p2
        # and dividing it by (h**2).
        return (p1 - 2*p2 + p3)/(h**2)

    def vega(self):
        """
        Calculate the vega of the option.

        The vega of an option represents the rate of change of the option's price with
        respect to the volatility of the underlying stock. If the volatility of the
        underlying stock increases, the vega will increase. If the volatility of the
        underlying stock decreases, the vega will decrease. The vega is a measure of the
        option's sensitivity to changes in volatility.

        This function calculates the vega of the option by taking the difference
        between the option price when the volatility of the underlying stock is
        increased by a small amount (h) and the option price when it is decreased by
        the same amount (h). It then divides the difference by (2*h*100) to get the
        vega of the option.

        Args:
            self (BlackandScholes): An instance of the BlackandScholes class.

        Returns:
            float: The vega of the option.
        """
        # Define the small amount to change the volatility of the underlying stock by
        h = VEGA_DIFFERENTIAL
        # Calculate the option price when the volatility of the underlying stock is
        # increased by h
        p1 = self.BS(self.S, self.K, self.T, self.impvol + h, self.r, self.q)
        # Calculate the option price when the volatility of the underlying stock is
        # decreased by h
        p2 = self.BS(self.S, self.K, self.T, self.impvol - h, self.r, self.q)
        # Calculate the vega of the option by taking the difference between p1 and p2
        # and dividing it by (2*h*100).
        return (p1-p2)/(2*h*100)

    def theta(self):
        """
        Calculate the theta of the option.

        The theta of an option represents the rate of change of the option's price with
        respect to time. If time passes, the theta will change. The theta is a measure of
        the option's sensitivity to changes in time.

        This function calculates the theta of the option by taking the difference
        between the option price when time is increased by a small amount (h) and the
        option price when time is decreased by the same amount (h). It then divides the
        difference by (2*h*365) to get the theta of the option.

        Args:
            self (BlackandScholes): An instance of the BlackandScholes class.

        Returns:
            float: The theta of the option.
        """
        # Define the small amount to change the time by
        h = THETA_DIFFERENTIAL
        # Calculate the option price when time is increased by h
        p1 = self.BS(self.S, self.K, self.T + h, self.impvol, self.r, self.q)
        # Calculate the option price when time is decreased by h
        p2 = self.BS(self.S, self.K, self.T - h, self.impvol, self.r, self.q)
        # Calculate the theta of the option by taking the difference between p1 and p2
        # and dividing it by (2*h*365).
        return (p1-p2)/(2*h*365)

    def rho(self):
        """
        Calculate the rho of the option.

        The rho of an option represents the rate of change of the option's price with
        respect to the risk free interest rate. If the risk free interest rate increases,
        the rho will increase. If the risk free interest rate decreases, the rho will
        decrease. The rho is a measure of the option's sensitivity to changes in the
        risk free interest rate.

        This function calculates the rho of the option by taking the difference
        between the option price when the risk free interest rate is increased by a small
        amount (h) and the option price when it is decreased by the same amount (h).
        It then divides the difference by (2*h*100) to get the rho of the option.

        Args:
            self (BlackandScholes): An instance of the BlackandScholes class.

        Returns:
            float: The rho of the option.
        """
        # Define the small amount to change the risk free interest rate by
        h = RHO_DIFFERENTIAL
        # Calculate the option price when the risk free interest rate is increased by h
        p1 = self.BS(self.S, self.K, self.T, self.impvol, self.r + h, self.q)
        # Calculate the option price when the risk free interest rate is decreased by h
        p2 = self.BS(self.S, self.K, self.T, self.impvol, self.r - h, self.q)
        # Calculate the rho of the option by taking the difference between p1 and p2
        # and dividing it by (2*h*100).
        return (p1-p2)/(2*h*100)

Wallstreet: Real time Stock and Option tools
--------------------------------------------

Wallstreet is a Python 3 library for monitoring and analyzing real time Stock and
Option data. Quotes are provided from the Google Finance API. Wallstreet requires
minimal input from the user, it uses available online data to calculate option
greeks and even scrapes the US Treasury website to get the current risk free rate.


Usage
-----

Stocks:

.. code-block:: Python

  from wallstreet import Stock, Call, Put

  >>> s = Stock('AAPL')
  >>> s.price
  96.44
  >>> s.price
  96.48
  >>> s.change
  -0.35
  >>> s.last_trade
  '21 Jan 2016 13:32:12'

Options:

.. code-block:: Python

  >>> g = Call('GOOG', d=12, m=2, y=2016, strike=700)
  >>> g.price
  38.2
  >>> g.implied_volatility()
  0.49222968442691889
  >>> g.delta()
  0.56522039722040063
  >>> g.vega()
  0.685034827159825
  >>> g.underlying.price
  706.59

Alternative construction:

.. code-block:: Python

  >>> g = Call('GOOG', d=12, m=2, y=2016)
  >>> g
  Call(ticker=GOOG, expiration='12-02-2016')
  >>> g.strikes
  (580, 610, 620, 630, 640, 650, 660, 670, 680, 690, 697.5, 700, 702.5, 707.5, 710, 712.5, 715, 720, ...)
  >>> g.set_strike(712.5)
  >>> g
  Call(ticker=GOOG, expiration='12-02-2016', strike=712.5)

or

.. code-block:: Python

  >>> g = Put("GOOG")
  'No options listed for given date, using 22-01-2016 instead'
  >>> g.expirations
  ['22-01-2016', '29-01-2016', '05-02-2016', '12-02-2016', '19-02-2016', '26-02-2016', '04-03-2016', ...]
  >>> g
  Put(ticker=GOOG, expiration='22-01-2016')

Yahoo Finance Support (keep in mind that YF quotes might be delayed):

.. code-block:: Python

    >>> apple = Stock('AAPL', source='yahoo')
    >>> call = Call('AAPL', strike=apple.price, source='yahoo')
    No options listed for given date, using '26-05-2017' instead
    No option for given strike, using 155 instead

Download historical data (requires pandas)

.. code-block:: Python

    s = Stock('BTC-USD')
    >>> df = s.historical(days_back=30, frequency='d')
    >>> df
             Date          Open          High           Low         Close     Adj Close      Volume
    0  2019-07-10  12567.019531  13183.730469  11569.940430  12099.120117  12099.120117  1554955347
    1  2019-07-11  12099.120117  12099.910156  11002.389648  11343.120117  11343.120117  1185222449
    2  2019-07-12  11343.120117  11931.910156  11096.610352  11797.370117  11797.370117   647690095
    3  2019-07-13  11797.370117  11835.870117  10827.530273  11363.969727  11363.969727   668325183
    4  2019-07-14  11363.969727  11447.919922  10118.849609  10204.410156  10204.410156   814667763
    5  2019-07-15  10204.410156  11070.179688   9877.019531  10850.259766  10850.259766   965178341
    6  2019-07-16  10850.259766  11025.759766   9366.820313   9423.440430   9423.440430  1140137759
    7  2019-07-17   9423.440430   9982.240234   9086.509766   9696.150391   9696.150391   965256823
    8  2019-07-18   9696.150391  10776.540039   9292.610352  10638.349609  10638.349609  1033842556
    9  2019-07-19  10638.349609  10757.410156  10135.160156  10532.940430  10532.940430   658190962
    10 2019-07-20  10532.940430  11094.320313  10379.190430  10759.419922  10759.419922   608954333
    11 2019-07-21  10759.419922  10833.990234  10329.889648  10586.709961  10586.709961   405339891
    12 2019-07-22  10586.709961  10676.599609  10072.070313  10325.870117  10325.870117   524442852
    13 2019-07-23  10325.870117  10328.440430   9820.610352   9854.150391   9854.150391   529438124
    14 2019-07-24   9854.150391   9920.540039   9535.780273   9772.139648   9772.139648   531611909
    15 2019-07-25   9772.139648  10184.429688   9744.700195   9882.429688   9882.429688   403576364
    16 2019-07-26   9882.429688   9890.049805   9668.519531   9847.450195   9847.450195   312717110
    17 2019-07-27   9847.450195  10202.950195   9310.469727   9478.320313   9478.320313   512612117
    18 2019-07-28   9478.320313   9591.519531   9135.639648   9531.769531   9531.769531   267243770
    19 2019-07-29   9531.769531   9717.690430   9386.900391   9506.929688   9506.929688   299936368
    20 2019-07-30   9506.929688   9749.530273   9391.780273   9595.519531   9595.519531   276402322
    21 2019-07-31   9595.519531  10123.940430   9581.599609  10089.250000  10089.250000   416343142
    22 2019-08-01  10089.250000  10488.809570   9890.490234  10409.790039  10409.790039   442037342
    23 2019-08-02  10409.790039  10666.639648  10340.820313  10528.990234  10528.990234   463688251
    24 2019-08-03  10528.990234  10915.000000  10509.349609  10820.410156  10820.410156   367536516
    25 2019-08-04  10820.410156  11074.950195  10572.240234  10978.910156  10978.910156   431699306
    26 2019-08-05  10978.910156  11945.379883  10978.889648  11807.959961  11807.959961   870917186
    27 2019-08-06  11807.959961  12316.849609  11224.099609  11467.099609  11467.099609   949534020
    28 2019-08-07  11467.099609  12138.549805  11393.980469  11974.280273  11974.280273   834719365
    29 2019-08-08  11974.280273  12042.870117  11498.040039  11982.799805  11982.799805   588463519
    30 2019-08-09  11983.620117  12027.570313  11674.059570  11810.679688  11810.679688   366160288

Installation
------------
Simply

.. code-block:: bash

    $ pip install wallstreet


Stock Attributes
----------------

- ticker
- price
- id
- exchange
- last_trade
- change   (change in currency)
- cp   (percentage change)


Option Attributes and Methods
-----------------------------

- strike
- expiration
- underlying  (underlying stock object)
- ticker
- bid
- ask
- price (option price)
- id
- exchange
- change  (in currency)
- cp  (percentage change)
- volume
- open_interest
- code
- expirations (list of possible expiration dates for option chain)
- strikes (list of possible strike prices)

- set_strike()
- implied_volatility()
- delta()
- gamma()
- vega()
- theta()
- rho()

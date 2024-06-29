
# Date format used for formatting and parsing dates.
DATE_FORMAT = '%d-%m-%Y'

# Date time format used for formatting and parsing dates and times.
DATETIME_FORMAT = '%d %b %Y %H:%M:%S'

# URL for the US Treasury yields website.
TREASURY_URL = "https://home.treasury.gov/sites/default/files/interest-rates/yield.xml"

# The difference in price that is used to calculate the delta of an option.
DELTA_DIFFERENTIAL = 1.e-3

# The difference in price that is used to calculate the vega of an option.
VEGA_DIFFERENTIAL = 1.e-4

# The difference in price that is used to calculate the gamma of an option.
GAMMA_DIFFERENTIAL = 1.e-3

# The difference in price that is used to calculate the rho of an option.
RHO_DIFFERENTIAL = 1.e-4

# The difference in time that is used to calculate the theta of an option.
THETA_DIFFERENTIAL = 1.e-5

# The tolerance used in the solver when calculating the implied volatility.
IMPLIED_VOLATILITY_TOLERANCE = 1.e-6

# The starting value used in the solver when calculating the implied volatility.
SOLVER_STARTING_VALUE = 0.27

# The risk free rate when the overnight rate cannot be determined.
OVERNIGHT_RATE = 0

# The risk free rate used as a fallback when the risk free rate cannot be determined.
FALLBACK_RISK_FREE_RATE = 0.02


from setuptools import setup

# Setup configuration for the project
setup(
    # Name of the project
    name='wallstreet',
    # Version of the project
    version='0.4.0',
    # Description of the project
    description='Real-time Stock and Option tools',
    # URL of the project
    url='https://github.com/mcdallas/wallstreet',
    # Author of the project
    author='Mike Dallas',
    # Author's email
    author_email='mcdallas@protonmail.com',
    # License under which the project is distributed
    license='MIT',
    # Packages included in the project
    packages=['wallstreet'],
    # Classifiers that describe the project's maturity and audience
    classifiers=[
        # Project maturity
        'Development Status :: 3 - Alpha',
        # Intended audience
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        # Topic of the project
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        # Operating system compatibility
        'Operating System :: OS Independent',
        # License of the project
        'License :: OSI Approved :: MIT License',
        # Supported Python versions
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    # Keywords associated with the project
    keywords='stocks options finance market shares greeks implied volatility real-time',
    # Dependencies of the project
    install_requires=['requests', 'scipy', 'yfinance'],
)

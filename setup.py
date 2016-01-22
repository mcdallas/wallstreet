from setuptools import setup

setup(
    name='wallstreet',
    version='0.1.5',
    description='Real-time Stock and Option tools',
    url='https://github.com/mcdallas/wallstreet',
    author='Mike Dallas',
    author_email='mc-dallas@hotmail.com',
    license='MIT',
    packages=['wallstreet'],
    classifiers=[
        # How mature is this project? Common values are
        # 3 - Alpha
        # 4 - Beta
        # 5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='stocks options finance market shares greeks implied volatility real-time',
    install_requires=['requests', 'beautifulsoup4'],
)

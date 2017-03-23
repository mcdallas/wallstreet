
from setuptools import setup

setup(
    name='mockrequests',
    version='0.1.2',
    description='Easy unit testing for HTTP requests',
    url='https://github.com/mcdallas/mockrequests',
    author='Mike Dallas',
    author_email='mc-dallas@hotmail.com',
    license='MIT',
    packages=['mockrequests'],
    classifiers=[
        # How mature is this project? Common values are
        # 3 - Alpha
        # 4 - Beta
        # 5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='requests mock unit test unit-test http',
    install_requires=['requests'],
)
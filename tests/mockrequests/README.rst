Mockrequests: Easy unit testing for HTTP requests
-------------------------------------------------

Mockrequests is a Python 3 library for unit testing code that makes HTTP requests
using the requests module. Simply monkey patch the imported requests module with
mockrequests when unittesting and everything else is done for you. Mockrequests
makes use of the unittest.mock module added in Python 3.3 so you will be able to
take advantage of its functionality.


Usage
-----

.. code-block:: Python

  import unittest
  from my_package import my_module
  import mockrequests

  class MyModuleTest(unittest.TestCase):
      def setUp(self):
          self.oldrequests = my_module.requests  # Make a backup of your requests import
          my_module.requests = mockrequests  # Replace the requests import with mockrequests

      def test_my_module(self):
          # blah blah

      def tearDown(self):
          my_module.requests = self.oldrequests  # Move the old requests back


Mockrequests will redirect all the HTTP request of your code to cached request objects that you
set up before.

Setup
-----

.. code-block:: Python

   import requests
   import mockrequests

   >>> r = requests.get('http://www.somewebsite.com/')
   >>> mockrequests.save(r)

   # That's it. Now every time you try to access this url you will get the cached response.

   >>> mockrequests.get('http://www.somewebsite.com/')
   <Response [200]>

If the url that your code tries to reach is not static (i.e it contains a date) then you can pass a regex expression and mockrequests will return the first saved url that matches the regex.

.. code-block:: Python

   >>> r = requests.get('http://www.google.com/')
   >>> mockrequests.save(r, regex='^.*google.*?')
   >>> mockrequests.get('http://www.google.co.uk/')
   <Response [200]>

You can also pass the strict=True parameter and you will get a response only if the HTTP headers match.

.. pyOutlook documentation master file, created by
   sphinx-quickstart on Sun Apr 24 17:49:58 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyOutlook's documentation!
=====================================
.. image:: https://img.shields.io/pypi/v/pyOutlook.svg?maxAge=2592000   :target:
.. image:: https://img.shields.io/pypi/pyversions/pyOutlook.svg?maxAge=2592000   :target:
.. image:: https://gitlab.com/jensastrup/pyOutlook/badges/master/coverage.svg
.. image:: https://img.shields.io/pypi/status/pyOutlook.svg?maxAge=2592000   :target:
.. image:: https://requires.io/github/JensAstrup/pyOutlook/requirements.svg?branch=master
     :target: https://requires.io/github/JensAstrup/pyOutlook/requirements/?branch=master
     :alt: Requirements Status

About:
------
pyOutlook was created after I found myself attempting to connect to the Outlook REST API in multiple projects. This
provided some much needed uniformity. It's easier to deal with than the win32com package by Microsoft, but obviously has
a far smaller scope.

Python Versions
_______________
pyOutlook is only tested in, and targets, Python 3.5, 3.6, and 2.7.

Recommended:
------------
pyOutlook does not handle OAuth for the access tokens provided by Outlook. These are provided by you via the OutlookAccount
class as a string. There are various OAuth packages out there: (pip install) oauth2, python-oauth2, requests_oauthlib, etc
that can facilitate the process.

Notes:
------
All protected & private methods and anything under pyOutlook.internal is subject to change without deprecation warnings

Contents:
---------
.. toctree::
   :maxdepth: 2

   installation
   quickstart
   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`


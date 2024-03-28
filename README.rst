#####################
Top.gg Python Library
#####################

.. image:: https://img.shields.io/pypi/v/topggpy.svg
   :target: https://pypi.python.org/pypi/topggpy
   :alt: View on PyPI
.. image:: https://img.shields.io/pypi/dm/topggpy?style=flat-square
   :target: https://topggpy.readthedocs.io/en/latest/?badge=latest
   :alt: Monthly PyPI downloads

A simple API wrapper for `Top.gg <https://top.gg/>`_ written in Python.

Installation
------------

.. code:: bash

    pip install topggpy

Documentation
-------------

Documentation can be found `here <https://topggpy.readthedocs.io/en/latest/>`_

Features
--------

* POST server count
* GET bot info, server count, upvote info
* GET user info
* GET widgets (large and small) including custom ones. See `docs.top.gg <https://docs.top.gg/>`_ for more info.
* GET weekend status
* Built-in webhook to handle Top.gg votes
* Automated server count posting
* Searching for bots via the API

Additional information
----------------------

* Before using the webhook provided by this library, make sure that you have specified port open.
* Optimal values for port are between 1024 and 49151.
* If you happen to need help implementing topggpy in your bot, feel free to ask in the ``#development`` or ``#api`` channels in our `Discord server <https://discord.gg/EYHTgJX>`_.

Examples
--------

For examples, follow the link `here <examples>`__
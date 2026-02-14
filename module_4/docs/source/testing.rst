Testing
=======

Run the full marked suite
-------------------------

.. code-block:: powershell

   python -m pytest -m "web or buttons or analysis or db or integration"

Coverage
--------

.. code-block:: powershell

   python -m pytest --cov=src --cov-report=term-missing

Markers
-------
- web
- buttons
- analysis
- db
- integration

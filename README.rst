==========
pimsclient
==========


.. image:: https://img.shields.io/pypi/v/pimsclient.svg
        :target: https://pypi.python.org/pypi/pimsclient

.. image:: https://img.shields.io/travis/sjoerdk/pimsclient.svg
        :target: https://travis-ci.org/sjoerdk/pimsclient

.. image:: https://readthedocs.org/projects/pimsclient/badge/?version=latest
        :target: https://pimsclient.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://api.codeclimate.com/v1/badges/aca3e6099b08a606075f/maintainability
       :target: https://codeclimate.com/github/sjoerdk/pimsclient/maintainability
       :alt: Maintainability

.. image:: https://codecov.io/gh/sjoerdk/pimsclient/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/sjoerdk/pimsclient

.. image:: https://pyup.io/repos/github/sjoerdk/pimsclient/shield.svg
     :target: https://pyup.io/repos/github/sjoerdk/pimsclient/
     :alt: Updates

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black



Client for PIMS keyfile management swagger web API.


* Free software: MIT license
* Documentation: https://pimsclient.readthedocs.io.


Features
--------

* Pseudonymize and reidentify using PIMS keyfile management as backend
* Supports multiple value types: PatientUID, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID, AccessionNumber
* Authentication via NTLM

Getting started
---------------
See `Usage <https://pimsclient.readthedocs.io/en/latest/usage.html>`

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

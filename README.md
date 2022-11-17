# pimsclient

[![CI](https://github.com/sjoerdk/pimsclient/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/sjoerdk/pimsclient/actions/workflows/build.yml?query=branch%3Amaster)
[![PyPI](https://img.shields.io/pypi/v/dicomtrolley)](https://pypi.org/project/dicomtrolley/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dicomtrolley)](https://pypi.org/project/dicomtrolley/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)


Client for PIMS keyfile management swagger web API.

* Free software: MIT license
* Pseudonymize and reidentify using PIMS keyfile management as backend
* Supports multiple value types: PatientUID, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID, AccessionNumber
* Authentication via NTLM

## Installation
```
pip install pimsclient
```
## Usage

### Basic example
To use pimsclient in a project

```
    from pimsclient.client import connect, PatientID, PseudoPatientID

    # Create a project connected to a certain PIMS key file
    project = connect('https://pims.radboudumc.nl/api',
                       pims_key_file_id=26)

    # I have some patientIDs I want to pseudonymize with PIMS
    keys = project.pseudonymize([PatientID('1234'),
                                 PatientID('5678'),
                                 PatientID('9012')])

    # I found some pseudo patientIDs. What was the original ID?
    keys = project.reidentify([PseudoPatientID('Patient1'),
                               PseudoPatientID('Patient2'),
                               PseudoPatientID('Patient3')])

```

### Credentials

Should be set in the environment using the keys

```
    PIMS_CLIENT_USER
    PIMS_CLIENT_PASSWORD
```


## Credits

This package was originally created with [Cookiecutter](https://github.com/audreyr/cookiecutter)
and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
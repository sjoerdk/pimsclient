# pimsclient

[![CI](https://github.com/sjoerdk/pimsclient/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/sjoerdk/pimsclient/actions/workflows/build.yml?query=branch%3Amaster)
[![PyPI](https://img.shields.io/pypi/v/pimsclient)](https://pypi.org/project/pimsclient/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pimsclient)](https://pypi.org/project/pimsclient/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)


Client for PIMS keyfile management swagger web API.

* Pseudonymize and reidentify using PIMS keyfile management as backend
* Supports multiple identity/pseudonym types:
  * PatientUID
  * StudyInstanceUID
  * SeriesInstanceUID
  * SOPInstanceUID
  * AccessionNumber
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


# Contributing
You can contribute in different ways

## Report bugs
Report bugs at https://github.com/sjoerdk/pimsclient/issues.

## Contribute code
### Get the code
Fork this repo, create a feature branch

### Set up environment
pimsclient uses [poetry](https://python-poetry.org/docs/) for dependency and package management 
* Install poetry (see [poetry docs](https://python-poetry.org/docs/#installation))
* Create a virtual env. Go to the folder where cloned pimsclient and use 
  ```  
  poetry install 
  ``` 
* Install [pre-commit](https://pre-commit.com) hooks.
  ```
  pre-commit install
  ```
  
### Add your code 
Make your code contributions. Make sure document and add tests for new features.
To automatically publish to pypi, increment the version number and push to master. See below. 

### Lint your code
* Run all tests
* Run [pre-commit](https://pre-commit.com):
  ```
  pre-commit run
  ```
### Publish
Create a pull request

### Incrementing the version number
A merged pull request will only be published to pypi if it has a new version number. 
To bump pimsclient's version, do the following.
* pimsclient uses [semantic versioning](https://semver.org/) Check whether your addition is a PATCH, MINOR or MAJOR version.
* Manually increment the version number:
  * `pyproject.toml` -> `version = "0.1.2"`
  
* Add a brief description of your updates new version to `HISTORY.md`

## Credits

This package was originally created with [Cookiecutter](https://github.com/audreyr/cookiecutter)
and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
# History
## 2.3.0 (2025-06-25)
* Relaxes JSON type checking so that unknown fields no longer trigger exceptions. Fixes #295

## 2.2.0 (2025-06-02)
* Moves from pydantic 1 to 2. Upgrades dependencies. Drops python 3.8

## 2.1.1 (2025-01-03)
* Adds KeyfileResponse.studyID parameter to API def. Fixes ResearchBureau/tickets#299

## 2.1.0 (2024-09-24)
* Adds Microsoft Authentication Library (MSAL) authorization with certificates, fixes #291

## 2.0.3 (2024-04-29)
* Truncates server error messages to 300 chars (refs #289)
  
## 2.0.2 (2024-04-24)
* Downgrades pydantic to 1.8.2 to ease adoption in older projects

## 2.0.0 (2024-04-24)
* Moves to support PIMS2 API
* Rewrites all tests, most backend code
* Adds Microsoft AD authentication
* Replaces main interaction object `Project` with `KeyFile`
* Skips major version 1 to align with PIMS version

## 0.7.0 (2022-11-18)
* Moves to poetry/pyproject.toml for packaging
* Removes external docs in favour of readme.md
* Bumps minimum python version to 3.8
* Adds flake8 and mypy linting

## 0.5.0 (2021-01-19)
* Adds AccessionNumber handling

## 0.1.0 (2019-05-23)
* First release on PyPI.

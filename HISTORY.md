# History
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

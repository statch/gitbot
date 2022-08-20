# The GitBot Library ⌨️
This directory includes the most essential building blocks of GitBot's entire service.

## Table of contents:
- `/api` - all the interfaces for interacting with 3rd party APIs (GitHub, PyPI, etc.)
- `/structs` - the most prominent of all the subdirectories, contains useful datatypes and custom implementations of discord.py objects
- `/typehints` - holds all the custom typehints used throughout the project, most importantly TypedDicts used for annotating database returns, but also certain locale values
- `/utils` - miscellaneous decorators, RegEx patterns, etc.
- `manager.py` - the centerpiece of the entire library, holds utility, locale, database, and network functions

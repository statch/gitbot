## Contributing
*Want to help out? This is how!*

1. [Create a bug report, feature request, or other issue](https://github.com/statch/gitbot/issues) and assign yourself.
2. Fork the repository, or create a new branch.
3. Make your changes, with descriptive commit names. Remember to follow the [style guide](#style-guide)!
4. [Create a pull request](https://github.com/statch/gitbot/pulls) with a detailed description of the issue resolved, link the issue you created, and request a reviewer.
5. One of the main devs will review it and request changes if needed!

## Style Guide
### General Guidelines
* Typehint wherever possible
* Use f-strings (`f'{thing}'`) instead of `.format()` where possible
* Use concatenation for uncomplicated things instead of f-strings, as concatenation is faster
* Unless there's a good reason, lines shouldn't be longer than 100 characters
* Use `snake_case` for variables and function names

### Functions/Methods
* Must have typehints for arguments and return type annotations for returns
* There should be two new lines before the start of a function unless it's indented
* If a method's return type is the method's class, do `from __future__ import annotations` to fix NameErrors

### Classes
* Names should be written using `PascalCase`
* There should be two new lines before the start of a class unless it's indented
* Must have typehints for `__init__` arguments

________

If in doubt, refer to the [Style Guide for Python Code (PEP8)](https://www.python.org/dev/peps/pep-0008/) 

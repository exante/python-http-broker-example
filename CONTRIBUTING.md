This file describes rules to contribute to EXANTE repositories

Docs
====

* Every method should have docstring with:
    * small description (`does foo`);
    * all available parameters descriptions. If there is default value it should
      be mentioned. Parameters types should be mentioned as well
      (`:param foo: foo, str. Default is 'bar'`);
    * return values (`:return: value, str`);
    * optional: usage example

Testing and logging
===================

* To logging your output use [logging library](https://docs.python.org/3/howto/logging.html)
  *info* is casual information, *debug* is verbose information which is not usually
  required, *warning* indicates possible non-critical errors, *error* is critical
  error. Do not use *critical* log type.
* All libraries (except for tool which work with external services maybe) should
  have own tests. Each method should be tested. Refer to
  http://docs.python-guide.org/en/latest/writing/tests/#py-test .
* Any changes in library should be accompanied by test run before commit.
* Any method should have description comment.

Code style
==========

The main code style is described [here](https://www.python.org/dev/peps/pep-0008/).
For automagic [autopep](https://pypi.python.org/pypi/autopep8) with options `-a -i`
is recommended. Some details below:

* Do not use lines more than 80 symbols.
* Avoid to use double quotes.
* Do not use lines more than 80 symbols.
* To concatenate use `format` method. More details: https://docs.python.org/3/library/string.html .
* You don't want to use lines more than 80 symbols.
* Library variables and methods are with `underline_symbol`. No `camelCase`.
  Classes should be named with `UpperCase`.
* Do not use hardcode.
* If you are using item twice or more - create method.
* Create tools which doesn't requires any system variables (for example `$PYTHONPATH`).
* Use one break line to separate method inside class, and two - outside.
* Almost all methods should return anything. `None` is not recommended.
* Do not use `print`, `pprint`, etc. Use `logging` instead.
* No dots and the end of comment otherwise we will find you by IP. And it should
  start with small letter. Seriously.
* No trailing spaces. It makes me nervous.

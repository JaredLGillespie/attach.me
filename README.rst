Attach Me
========

.. image:: https://img.shields.io/travis/JaredLGillespie/attach.me.svg
    :alt: Travis
    :target: https://travis-ci.org/JaredLGillespie/attach.me
.. image:: https://img.shields.io/coveralls/github/JaredLGillespie/attach.me.svg
    :alt: Coveralls github
    :target: https://coveralls.io/github/JaredLGillespie/attach.me
.. image:: https://img.shields.io/pypi/v/attach.me.svg
    :alt: PyPI
    :target: https://pypi.org/project/attach.me/
.. image:: https://img.shields.io/pypi/wheel/attach.me.svg
    :alt: PyPI - Wheel
    :target: https://pypi.org/project/attach.me/
.. image:: https://img.shields.io/pypi/pyversions/attach.me.svg
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/attach.me/
.. image:: https://img.shields.io/pypi/l/attach.me.svg
    :alt: PyPI - License
    :target: https://pypi.org/project/attach.me/

A library for attaching additional functionality around existing functions, such as before or after execution, or given
a raised exception or specific return value.

.. code-block:: python

    @attach(on_before=lambda: print('Initializing connection'),
              on_after=lambda: print('Connect successfully established'),
              on_error=lambda x: print('Erred establishing connection: %s' % x),
              on_return=lambda x: print('Returned connection: %s' % x))
    def connection(conn_str, params):
        conn = db(conn_str, params)
        return db.open()

Installation
------------

The latest version of attach.me is available via ``pip``:

.. code-block:: python

    pip install attach.me

Alternatively, you can download and install from source:

.. code-block:: python

    python setup.py install

Getting Started
---------------

The ``attach`` function contains the following signature:

.. code-block:: python

    def attach(on_before=None, on_after=None, on_error=None, on_return=None,
                 override_error=False, override_return=False, before_has_kwargs=False):
        ...

It serves as both a function decorator, and a runnable wrapper and is configurable through it's dynamic parameters. Most
of which are function callbacks which allow the user to highly configure the retrying behavior.

Before / After Execution
^^^^^^^^^^^^^^^^

Either prior to the wrapped function being executed, or afterwards, another function can be called. The most simplistic
use case for this is logging the beginning and ending of execution of a function.

.. code-block:: python

    @attach(on_before=lambda: logging.info('Execution began'),
                 on_after=lambda: logging.info('Execution ended')):
    def func():
        ...

If an exception is raised by the wrapped function (or the ``on_before`` function), the ``on_after`` function isn't
called

More complex usage comes from digesting the parameters meant for the wrapped function and transforming them in some way.
This is accomplished by simply returning an object from the ``on_before`` function and the values will be used instead
of the ones passed in.

.. code-block:: python

    def sanitize(string):
        # Do some stuff
        return new_string

    @attach(on_before=lambda x: sanitize(x)):
    def func(string):
        ...

If an iterable is returned, it is used as the *args of the wrapped function. The ``before_with_kwargs`` argument can be
set to ``True`` to specify that the return value be used as the **kwargs of the wrapped function (which means it should
be a dictionary. If an iterable is returned and this parameter is set, the last value is used as the **kwargs, and the
rest as the *args.

.. code-block:: python

    def sanitize(string):
        # Do some stuff
        return new_string

    @attach(on_before=lambda x: sanitize(x), {'use_ssl': True})
    def func(string):
        ...

Error Handling
^^^^^^^^^^^^^^

The ``on_error`` can be used to execute a function if an exception is raised. By default, the original exception is
still raised after the ``on_error`` callback is called. This can be changed by setting ``override_error`` to ``True``.
This can be used to instead return a value or raise a different exception.

.. code-block:: python

    def on_error(e):
        print('Caught error: ' + str(e))
        if isinstance(e, TypeError):
            return -1
        raise

    @attach(on_error=on_error, override_error=True)
    def func():
        raise TypeError

    # -1 is returned instead of raising TypeError

Return Value Handling
^^^^^^^^^^^^^^^^^^^^^

Like raised exception, return values can consumed by a ``on_return`` function in a similar manner. By default, the
original return value is still returned after the ``on_return`` callback is called. This can be changed by setting
``override_return`` to ``True``. A common use case for this is when interacting with functions that yield a return value
that indicates a failed state (like ``-1`` or ``None``), while other values indicate a successful state (like ``0`` or
an ``object``). This behavior can be transformed into a simple bool ``True`` or ``False`` return value instead.

.. code-block:: python

    def on_return(val):
        if val in (-1, None):
            return False
        return True

    @attach(on_return=on_return, override_return=True)
    def func()
        return -1

    # False is returned instead of -1

If an exception is raised by the wrapped function (or the ``on_before`` or ``on_after`` functions), the ``on_return``
function isn't called.

Advanced Usage
--------------

Instead of using as a decorator, ``attach`` can be used as an instead for wrapping an arbitrary number of function
calls. This can be achieved via the ``run`` method.

.. code-block:: python

    def func_a():
        ...

    def func_b():
        ...

    attacher = attach(on_before=..., on_after=..., on_error=..., on_return=...)

    # Using same configured attach instance
    attach.run(func_a, args, kwargs)
    attach.run(func_b, args, kwargs)

Besides using the provided ``run`` method, like any decorator functions can be locally wrapped, passed around, and
executed.

.. code-block:: python

    def func():
        ...

    attacher = attach(on_before=..., on_after=..., on_error=..., on_return=...)
    attach_func = attacher(func)
    attach_func(args, kwargs)

    # Or as a one-off like so
    attach(...)(func)(args, kwargs)

Each of the function parameters that can be passed into ``attach``, can actually be configured to accepts different
number of parameters depending on the function. They can each either accept 0 parameters, the parameters that would be
typically passed in, or the wrapped function's args and kwargs in addition to the parameters typically given.

Optionally passing in the args and kwargs allows for building more complex callback functions. Each of the possible
function variations are shown below.

.. code-block:: python

    def on_before(): ...
    def on_before(*args, **kwargs): ...

    def on_after(): ...
    def on_after(*args, **kwargs): ...

    def on_error(): ...
    def on_error(error): ...
    def on_error(error, *args, **kwargs): ...

    def on_return(): ...
    def on_return(value): ...
    def on_return(value, *args, **kwargs): ...

Contribution
------------

Contributions or suggestions are welcome! Feel free to `open an issue`_ if a bug is found or an enhancement is desired,
or even a `pull request`_.

.. _open an issue: https://github.com/jaredlgillespie/attach.me/issues
.. _pull request: https://github.com/jaredlgillespie/attach.me/compare

Changelog
---------

All changes and versioning information can be found in the `CHANGELOG`_.

.. _CHANGELOG: https://github.com/JaredLGillespie/attach.me/blob/master/CHANGELOG.rst

License
-------

Copyright (c) 2018 Jared Gillespie. See `LICENSE`_ for details.

.. _LICENSE: https://github.com/JaredLGillespie/attach.me/blob/master/LICENSE.txt

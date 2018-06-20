# MIT License
#
# Copyright (c) 2018 Jared Gillespie
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Function decorator for attaching additional functionality, such as before or after execution, or given a raised
exception or specific return value.
This exports:
  - attach is the function decorator
"""

from inspect import signature, Parameter
from functools import wraps


class _FunctionSignature:
    """Flags for parameters accepted by function signature."""
    NORMAL = 1 << 0
    ARGS = 1 << 1
    KWARGS = 1 << 2


class attach:
    """Functionality attachment decorator.

    Wraps a function and allows attaching additional functionality before and after execution, as well as in the event
    of an exception being raised or value being returned.

    Each of the functions that can be passed in (`on_before`, `on_after`, `on_error`, `on_return`, and `on_retry`) can
    either accept 0 parameters, the number of parameters as described below, or the wrapped function's args and
    kwargs in addition to the parameters as described below.

    For usage examples, see https://github.com/JaredLGillespie/attach.me.

    :param on_before:
        A callable function to be called before the execution of the wrapped function. If a return value other than None
        is returned, then the returned values are used instead of those passed to the wrapped function. By default,
        all the values returned are used as args; however the `before_has_kwargs` argument can be used to use the last
        value returned as kwargs. If None is desired to be passed to the function, a sequence containing the single
        element None should be used.
    :param on_after:
        A callable function to be called after the execution of the wrapped function.
    :param on_error:
        A callable function which accepts a single value (the error) which is raised.
    :param on_return:
        A callable function which accepts a single value (the return value) which is returned.
    :param override_error:
        A boolean value indicating whether to raise the exception caught from the `on_error` callback or not. True
        indicates to not raise the exception, while False indicates to raise it. If no `on_error` callback is given,
        this has no effect.
    :param override_return:
        A boolean value indicating whether to return the value from the original function caught from the `on_return`
        callback or not. True indicates to return the original value, while False indicates to return the value returned
        from the callback function instead.
    :param before_has_kwargs:
        A boolean value indicating whether the return value of before represents a kwargs argument. If a collection of
        values is returned, then the last element is considered the kwargs and the first the args.
    :type on_before: callable
    :type on_after: callable
    :type on_error: callable
    :type on_return: callable
    :type override_error: bool
    :type override_return: bool
    :type before_has_kwargs: bool
    """
    def __init__(self, on_before=None, on_after=None, on_error=None, on_return=None,
                 override_error=False, override_return=False, before_has_kwargs=False):
        self.on_before = on_before
        self.on_after = on_after
        self.on_error = on_error
        self.on_return = on_return
        self.override_error = override_error
        self.override_return = override_return
        self.before_has_kwargs = before_has_kwargs

        # Signatures
        self._sig_before = None if not callable(on_before) else self._define_function_signature(on_before)
        self._sig_after = None if not callable(on_after) else self._define_function_signature(on_after)
        self._sig_error = None if not callable(on_error) else self._define_function_signature(on_error)
        self._sig_return = None if not callable(on_return) else self._define_function_signature(on_return)

    def __call__(self, func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            return self.run(func, *args, **kwargs)

        return func_wrapper

    def run(self, func, *args, **kwargs):
        """Executes a function using this as the wrapper.

        :param func:
            A function to wrap and call.
        :param args:
            Arguments to pass to the function.
        :param kwargs:
            Keyword arguments to pass to the function.
        :type func: function
        """
        try:
            if self.on_before is not None and callable(self.on_before):
                new_ret = self._call_with_sig(self.on_before, self._sig_before, (), *args, **kwargs)
                if new_ret is not None:
                    args, kwargs = self._convert_before_return(new_ret)

            ret = func(*args, **kwargs)

            if self.on_after is not None and callable(self.on_after):
                self._call_with_sig(self.on_after, self._sig_before, (), *args, **kwargs)

            if self.on_return is not None and callable(self.on_return):
                new_ret = self._call_with_sig(self.on_return, self._sig_return, (ret,), *args, **kwargs)
                if self.override_return:
                    return new_ret

            return ret
        except Exception as e:
            if self.on_error is not None and callable(self.on_error):
                new_ret = self._call_with_sig(self.on_error, self._sig_error, (e,), *args, **kwargs)
                if self.override_error:
                    return new_ret

            raise

    def _call_with_sig(self, func, sig, internal_args, *args, **kwargs):
        if not sig:
            return func()
        elif sig & (_FunctionSignature.ARGS | _FunctionSignature.KWARGS):
            return func(*(internal_args + args), **kwargs)
        else:
            return func(*internal_args)

    def _convert_before_return(self, value):
        if self._is_iterable(value) and not isinstance(value, dict):
            value = tuple(value)

            if self.before_has_kwargs:
                return value[:-1], value[-1]
            return value, {}

        if self.before_has_kwargs:
            return (), value
        return (value,), {}

    def _define_function_signature(self, func):
        sig = None

        for param in signature(func).parameters.values():
            if param.kind == Parameter.POSITIONAL_OR_KEYWORD:
                sig = (sig or _FunctionSignature.NORMAL) | _FunctionSignature.NORMAL
            elif param.kind == Parameter.VAR_KEYWORD:
                sig = (sig or _FunctionSignature.KWARGS) | _FunctionSignature.KWARGS
            elif param.kind == Parameter.VAR_POSITIONAL:
                sig = (sig or _FunctionSignature.ARGS) | _FunctionSignature.ARGS

        return sig

    def _is_iterable(self, obj):
        try:
            iter(obj)
            return True
        except TypeError:
            return False

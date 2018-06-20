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

import unittest
from unittest.mock import Mock
from inspect import isclass
from functools import partial, partialmethod
from attachme import attach


# Test helpers
def func(val, *args, **kwargs):
    if isclass(val) and issubclass(val, Exception):
        raise val

    if args:
        if kwargs:
            return (val,) + args, kwargs
        return (val,) + args

    if kwargs:
        return val, kwargs
    return val


partial_func = partial(func)


class Dummy:

    @classmethod
    def class_func(cls, val):
        return func(val)

    @staticmethod
    def static_func(val):
        return func(val)

    def func(self, val):
        return func(val)

    partial_func = partialmethod(func)


class TestAttach(unittest.TestCase):

    def test_no_handlers_success(self):
        out = attach()(func)(1)
        self.assertEqual(1, out)

    def test_no_handlers_error(self):
        with self.assertRaises(ValueError):
            attach()(func)(ValueError)

    def test_on_before(self):
        call = Mock()

        def on_before():
            call()

        out = attach(on_before=on_before)(func)(1)
        self.assertEqual(1, out)
        call.assert_called_once_with()

    def test_on_before_single_value_return(self):
        on_before = lambda: 4
        out = attach(on_before=on_before)(func)(1)
        self.assertEqual(4, out)

    def test_on_before_iterable_value_return(self):
        on_before = lambda: (2, 3)
        out = attach(on_before=on_before)(func)(2)
        self.assertEqual((2, 3), out)

    def test_on_before_single_value_kwargs(self):
        on_before = lambda: {'key': 1}

        def func(*args, **kwargs):
            if args and kwargs:
                return args, kwargs
            if args:
                return args
            return kwargs

        out = attach(on_before=on_before, before_has_kwargs=True)(func)(3)
        self.assertEqual({'key': 1}, out)

    def test_on_before_iterable_value_kwargs(self):
        on_before = lambda: (2, {'key': 1})
        out = attach(on_before=on_before, before_has_kwargs=True)(func)(3)
        self.assertEqual((2, {'key': 1}), out)

    def test_on_after(self):
        call = Mock()
        on_after = lambda: call()

        out = attach(on_after=on_after)(func)(1)
        self.assertEqual(1, out)
        call.assert_called_once_with()

    def test_on_error(self):
        call = Mock()
        on_error = lambda x: call(x)

        with self.assertRaises(ValueError):
            attach(on_error=on_error)(func)(ValueError)

        call.assert_called_once()

    def test_on_return(self):
        call = Mock()
        on_return = lambda x: call(x)

        out = attach(on_return=on_return)(func)(0)
        self.assertEqual(0, out)
        call.assert_called_once_with(0)

    def test_override_error(self):
        def on_error(error):
            return 0

        out = attach(on_error=on_error, override_error=True)(func)(ValueError)
        self.assertEqual(0, out)

    def test_override_error_with_error(self):
        def on_error(error):
            raise TypeError

        with self.assertRaises(TypeError):
            attach(on_error=on_error, override_error=True)(func)(ValueError)

    def test_override_return(self):
        on_return = lambda: 0

        out = attach(on_return=on_return, override_return=True)(func)(1)
        self.assertEqual(0, out)

    def test_partial_success(self):
        on_return = lambda: 0
        out = attach(on_return=on_return, override_return=True)(partial_func)(1)
        self.assertEqual(0, out)

    def test_partial_failure(self):
        call = Mock()
        on_error = lambda: call()

        with self.assertRaises(ValueError):
            attach(on_return=on_error)(partial_func)(ValueError)

    def test_method(self):
        on_return = lambda: 0
        out = attach(on_return=on_return, override_return=True)(Dummy().func)(1)
        self.assertEqual(0, out)

    def test_class_method(self):
        on_return = lambda: 0
        out = attach(on_return=on_return, override_return=True)(Dummy.class_func)(1)
        self.assertEqual(0, out)

    def test_static_method(self):
        on_return = lambda: 0
        out = attach(on_return=on_return, override_return=True)(Dummy.static_func)(1)
        self.assertEqual(0, out)

    def test_partial_method(self):
        on_return = lambda: 0
        out = attach(on_return=on_return, override_return=True)(Dummy().partial_func)(1)
        self.assertEqual(0, out)

    def test_run(self):
        call_error = Mock()
        call_return = Mock()
        on_error = lambda: call_error()
        on_return = lambda: call_return()

        decorator = attach(on_error=on_error, on_return=on_return)
        out = decorator.run(func, 0)
        self.assertEqual(0, out)

        with self.assertRaises(ValueError):
            decorator.run(func, ValueError)

    def test_handler_with_args(self):
        call = Mock()

        def on_return(x, *args):
            self.assertEqual(len(args), 1)
            call(x)

        out = attach(on_return=on_return)(func)(1)
        self.assertEqual(1, out)
        call.assert_called_once_with(1)

    def test_handler_with_args_and_kwargs(self):
        call = Mock()

        def on_return(x, *args, **kwargs):
            self.assertEqual(len(args), 1)
            self.assertEqual(len(kwargs), 1)
            call(x)

        out = attach(on_return=on_return)(func)(1, nothing=True)
        self.assertEqual((1, {'nothing': True}), out)
        call.assert_called_once_with((1, {'nothing': True}))

    def test_function_kwarg_only_params(self):
        call = Mock()

        def on_return(*args, x=1, **kwargs):
            call()

        out = attach(on_return=on_return)(func)(1)
        self.assertEqual(1, out)
        call.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()

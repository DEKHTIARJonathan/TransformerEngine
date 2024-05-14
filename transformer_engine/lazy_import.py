#! /usr/bin/python
# -*- coding: utf-8 -*-
"""This module provides lazy import functionality to improve the import
performance of nitime. For example, some parts of nitime leverage and import
matplotlib, which is quite a big package, yet most of the nitime code does not
depend on matplotlib. By lazily-loading a module, we defer the overhead of
importing it until the first time it is actually used, thereby speeding up
nitime imports.

A generic :class:`LazyImport` class is implemented which takes the module name
as a parameter, and acts as a proxy for that module, importing it only when
the module is used, but effectively acting as the module in every other way
(including inside IPython with respect to introspection and tab completion)
with the *exception* of reload() - reloading a :class:`LazyImport` raises an
:class:`ImportError`.

Commonly used nitime lazy imports are also defined in :mod:`nitime.lazy`, so
they can be reused throughout nitime.
"""

import os
import sys
import types


import importlib
import importlib.util


class _LazyImport_FlavorA(types.ModuleType):
    """
    This class takes the module name as a parameter, and acts as a proxy for
    that module, importing it only when the module is used, but effectively
    acting as the module in every other way (including inside IPython with
    respect to introspection and tab completion) with the *exception* of
    reload()- reloading a :class:`LazyImport` raises an :class:`ImportError`.

    >>> mlab = LazyImport('matplotlib.mlab')

    No import happens on the above line, until we do something like call an
    ``mlab`` method or try to do tab completion or introspection on ``mlab``
    in IPython.

    >>> mlab
    <module 'matplotlib.mlab' will be lazily loaded>

    Now the :class:`LazyImport` will do an actual import, and call the dist
    function of the imported module.

    >>> mlab.dist(1969,2011)
    42.0
    """

    def __getattribute__(self, x):
        # This method will be called only once, since we'll change
        # self.__class__ to LoadedLazyImport, and __getattribute__ will point
        # to module.__getattribute__

        name = object.__getattribute__(self, "__name__")
        __import__(name)

        # if name above is 'package.foo.bar', package is returned, the docs
        # recommend that in order to get back the full thing, that we import
        # and then lookup the full name is sys.modules, see:
        # http://docs.python.org/library/functions.html#__import__

        module = sys.modules[name]

        # Now that we've done the import, cutout the middleman and make self
        # act as the imported module

        class LoadedLazyImport(types.ModuleType):
            __getattribute__ = module.__getattribute__
            __repr__ = module.__repr__

        object.__setattr__(self, "__class__", LoadedLazyImport)

        # The next line will make "reload(l)" a silent no-op
        return module.__getattribute__(x)

    def __repr__(self):
        return f"<module '{object.__getattribute__(self, '__name__')}' will be lazily loaded>"


class _LazyImport_FlavorB(types.ModuleType):
    """Lazily import a module, mainly to avoid pulling in large dependencies.

    `contrib`, and `ffmpeg` are examples of modules that are large and not always
    needed, and this allows them to only be loaded when they are used.
    """

    # The lint error here is incorrect.
    def __init__(self, name, parent_module_globals=None):  # pylint: disable=super-on-old-class
        if parent_module_globals is None:
            parent_module_globals = globals()
        local_name = name.split(".")[-1]
        self._local_name = local_name
        self._parent_module_globals = parent_module_globals

        super().__init__(name)

    def _load(self):
        # Import the target module and insert it into the parent's namespace
        module = importlib.import_module(self.__name__)
        self._parent_module_globals[self._local_name] = module

        # Update this object's dict so that if someone keeps a reference to the
        #   LazyLoader, lookups are efficient (__getattr__ is only called on lookups
        #   that fail).
        self.__dict__.update(module.__dict__)

        return module

    def __getattr__(self, item):
        module = self._load()
        return getattr(module, item)

    def __dir__(self):
        module = self._load()
        return dir(module)


def _LazyImport_FlavorC(name: str) -> types.ModuleType:
    """Construct a module that is imported the first time it is used"""
    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


_LazyImportFlavor = int(os.environ.get("TE_LAZY_IMPORT_FLAVOR", "1"))

if _LazyImportFlavor == 1:
    LazyImport = _LazyImport_FlavorA
elif _LazyImportFlavor == 2:
    LazyImport = _LazyImport_FlavorB
elif _LazyImportFlavor == 3:
    LazyImport = _LazyImport_FlavorC
else:
    raise ValueError(
        f"Unknown `TE_LAZY_IMPORT_FLAVOR` value received: {_LazyImportFlavor}"
    )

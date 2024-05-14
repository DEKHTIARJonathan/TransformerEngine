# Copyright (c) 2022-2024, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# See LICENSE for license information.

"""Top level package"""

from transformer_engine import common
from transformer_engine._version import __version__
from transformer_engine.lazy_import import LazyImport


pytorch = LazyImport("transformer_engine.pytorch")
jax = LazyImport("transformer_engine.jax")
paddle = LazyImport("transformer_engine.paddle")


__all__ = [
    "__version__",
    "common",
    "jax",
    "paddle",
    "pytorch",
]

"""This module implements various utilities."""

from collections.abc import Callable


def bit_getter(index: int) -> Callable[[int], bool]:
    return lambda value: bool(value & (1 << index))

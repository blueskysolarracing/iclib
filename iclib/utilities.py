"""This module implements various utilities."""

from collections.abc import Callable


def bit_getter(index: int) -> Callable[[int], bool]:
    return lambda value: bool(value & (1 << index))


def twos_complement(value: int, bit_count: int) -> int:
    if value & (1 << (bit_count - 1)):
        value -= (1 << bit_count)

    return value

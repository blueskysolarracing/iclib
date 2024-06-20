"""This module implements various utilities."""

from collections.abc import Callable


def bit_getter(index: int) -> Callable[[int], bool]:
    return lambda value: bool(value & (1 << index))


def twos_complement(value: int, bit_count: int) -> int:
    if value & (1 << (bit_count - 1)):
        value -= (1 << bit_count)

    return value


def lsb_bits_to_byte(*bits: bool) -> int:
    byte = 0

    for i, bit in enumerate(bits):
        byte |= bit << i

    return byte


def msb_bits_to_byte(*bits: bool) -> int:
    byte = 0

    for bit in bits:
        byte <<= 1
        byte |= bit

    return byte

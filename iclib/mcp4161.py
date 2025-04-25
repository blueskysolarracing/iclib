"""This module implements the MCP4161 driver."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar
from warnings import warn

from periphery import SPI

from iclib.utilities import bit_getter


class MemoryAddress(IntEnum):
    """The enum class for memory addresses."""

    VOLATILE_WIPER_0 = 0x00
    """The volatile wiper 0."""
    VOLATILE_WIPER_1 = 0x01
    """The volatile wiper 0."""
    NON_VOLATILE_WIPER_0 = 0x02
    """The non-volatile wiper 0."""
    NON_VOLATILE_WIPER_1 = 0x03
    """The non-volatile wiper 1."""
    VOLATILE_TCON_REGISTER = 0x04
    """The volatile TCON register."""
    STATUS_REGISTER = 0x05
    """The status register."""


class STATUSBit(int):
    """The class for STATUS bits."""

    EEWA = property(bit_getter(4))
    """Get the EEWA bit."""
    WL1 = property(bit_getter(3))
    """Get the WL1 bit."""
    WL0 = property(bit_getter(2))
    """Get the WL0 bit."""
    SHDN = property(bit_getter(1))
    """Get the SHDN bit."""
    WP = property(bit_getter(0))
    """Get the WP bit."""


class TCONBit(int):
    """The class for TCON bits."""

    R1HW = property(bit_getter(7))
    """Get the R1HW bit."""
    R1A = property(bit_getter(6))
    """Get the R1A bit."""
    R1W = property(bit_getter(5))
    """Get the R1W bit."""
    R1B = property(bit_getter(4))
    """Get the R1B bit."""
    R0HW = property(bit_getter(3))
    """Get the R0HW bit."""
    R0A = property(bit_getter(2))
    """Get the R0A bit."""
    R0W = property(bit_getter(1))
    """Get the R0W bit."""
    R0B = property(bit_getter(0))
    """Get the R0B bit."""


@dataclass
class Command(ABC):
    """The abstract base class class for commands."""

    MEMORY_ADDRESS_OFFSET: ClassVar[int] = 4
    """The memory address offset for the command byte."""
    COMMAND_BITS_OFFSET: ClassVar[int] = 2
    """The command bits offset for the command byte."""
    COMMAND_BITS: ClassVar[int]
    """The command bits."""
    memory_address: int
    """The memory address."""

    @property
    @abstractmethod
    def transmitted_data_bytes(self) -> list[int]:
        """Return the transmitted data bytes.

        :return: The transmitted data bytes.
        """
        pass

    @abstractmethod
    def parse_received_data_bytes(self, data_bytes: list[int]) -> int | None:
        """Parse the received data bytes.

        :return: The received data bytes.
        """
        pass


@dataclass
class SixteenBitCommand(Command, ABC):
    """The abstract base class for 8-bit commands."""

    pass


@dataclass
class Read(SixteenBitCommand):
    """The class for read commands."""

    COMMAND_BITS: ClassVar[int] = 0b11
    READ_DATA_BIT_COUNT: ClassVar[int] = 9
    """The number of read data bits."""

    @property
    def transmitted_data_bytes(self) -> list[int]:
        return [
            (
                (self.memory_address << self.MEMORY_ADDRESS_OFFSET)
                | (self.COMMAND_BITS << self.COMMAND_BITS_OFFSET)
                | ((1 << self.COMMAND_BITS_OFFSET) - 1)
            ),
            (1 << MCP4161.SPI_WORD_BIT_COUNT) - 1,
        ]

    def parse_received_data_bytes(self, data_bytes: list[int]) -> int:
        return (
            ((data_bytes[0] << MCP4161.SPI_WORD_BIT_COUNT) | data_bytes[1])
            & ((1 << self.READ_DATA_BIT_COUNT) - 1)
        )


@dataclass
class Write(SixteenBitCommand):
    """The class for write commands."""

    COMMAND_BITS: ClassVar[int] = 0b00
    data: int
    """The data."""

    @property
    def transmitted_data_bytes(self) -> list[int]:
        return [
            (
                (self.memory_address << self.MEMORY_ADDRESS_OFFSET)
                | (self.COMMAND_BITS << self.COMMAND_BITS_OFFSET)
                | (self.data >> MCP4161.SPI_WORD_BIT_COUNT)
            ),
            self.data & ((1 << MCP4161.SPI_WORD_BIT_COUNT) - 1),
        ]

    def parse_received_data_bytes(self, data_bytes: list[int]) -> None:
        return None


@dataclass
class EightBitCommand(Command, ABC):
    """The abstract base class for 8-bit commands."""

    @property
    def transmitted_data_bytes(self) -> list[int]:
        return [
            (self.memory_address << self.MEMORY_ADDRESS_OFFSET)
            | (self.COMMAND_BITS << self.COMMAND_BITS_OFFSET),
        ]


@dataclass
class Increment(EightBitCommand):
    """The class for increment commands."""

    COMMAND_BITS: ClassVar[int] = 0b01

    def parse_received_data_bytes(self, data_bytes: list[int]) -> None:
        return None


@dataclass
class Decrement(EightBitCommand):
    """The class for decrement commands."""

    COMMAND_BITS: ClassVar[int] = 0b10

    def parse_received_data_bytes(self, data_bytes: list[int]) -> None:
        return None


@dataclass
class MCP4161:
    """A Python driver for Microchip Technology MCP4161 7/8-Bit
    Single/Dual SPI Digital POT with Non-Volatile Memory
    """

    SPI_MODES: ClassVar[tuple[int, int]] = 0b00, 0b11
    """The supported spi mode."""
    MAX_SPI_MAX_SPEED: ClassVar[float] = 10e6
    """The supported maximum spi maximum speed."""
    SPI_BIT_ORDER: ClassVar[str] = 'msb'
    """The supported spi bit order."""
    SPI_WORD_BIT_COUNT: ClassVar[int] = 8
    """The supported spi number of bits per word."""
    STEP_RANGE: ClassVar[range] = range(257)
    """The step range."""
    spi: SPI
    """The SPI."""

    def __post_init__(self) -> None:
        if self.spi.mode not in self.SPI_MODES:
            raise ValueError('unsupported spi mode')
        elif self.spi.max_speed > self.MAX_SPI_MAX_SPEED:
            raise ValueError('unsupported spi maximum speed')
        elif self.spi.bit_order != self.SPI_BIT_ORDER:
            raise ValueError('unsupported spi bit order')
        elif self.spi.bits_per_word != self.SPI_WORD_BIT_COUNT:
            raise ValueError('unsupported spi number of bits per word')

        if self.spi.extra_flags:
            warn(f'unknown spi extra flags {self.spi.extra_flags}')

    @property
    def VOLATILE_WIPER_0(self) -> int:
        """Read the VOLATILE_WIPER_0 register.

        :return: The register value.
        """
        return self.read(MemoryAddress.VOLATILE_WIPER_0)

    @VOLATILE_WIPER_0.setter
    def VOLATILE_WIPER_0(self, value: int) -> None:
        """Write to the VOLATILE_WIPER_0 register.

        :param value: The value.
        :return: ``None``.
        """
        self.write(MemoryAddress.VOLATILE_WIPER_0, value)

    @property
    def NON_VOLATILE_WIPER_0(self) -> int:
        """Read the NON_VOLATILE_WIPER_0 register.

        :return: The register value.
        """
        return self.read(MemoryAddress.NON_VOLATILE_WIPER_0)

    @NON_VOLATILE_WIPER_0.setter
    def NON_VOLATILE_WIPER_0(self, value: int) -> None:
        """Write to the NON_VOLATILE_WIPER_0 register.

        :param value: The value.
        :return: ``None``.
        """
        self.write(MemoryAddress.NON_VOLATILE_WIPER_0, value)

    @property
    def VOLATILE_TCON_REGISTER(self) -> TCONBit:
        """Read the VOLATILE_TCON_REGISTER register.

        :return: The register value.
        """
        return TCONBit(self.read(MemoryAddress.VOLATILE_TCON_REGISTER))

    @VOLATILE_TCON_REGISTER.setter
    def VOLATILE_TCON_REGISTER(self, value: int) -> None:
        """Write to the VOLATILE_TCON_REGISTER register.

        :param value: The value.
        :return: ``None``.
        """
        self.write(MemoryAddress.VOLATILE_TCON_REGISTER, value)

    @property
    def STATUS_REGISTER(self) -> STATUSBit:
        """Read the STATUS_REGISTER register.

        :return: The register value.
        """
        return STATUSBit(self.read(MemoryAddress.STATUS_REGISTER))

    @STATUS_REGISTER.setter
    def STATUS_REGISTER(self, value: int) -> None:
        """Write to the STATUS_REGISTER register.

        :param value: The value.
        :return: ``None``.
        """
        self.write(MemoryAddress.STATUS_REGISTER, value)

    def command(self, *commands: Command) -> list[int | None]:
        """Apply the commands.

        :param commands: The commands.
        :return: The received data.
        """
        transmitted_data_bytes = []

        for command in commands:
            transmitted_data_bytes.extend(command.transmitted_data_bytes)

        received_data_bytes = self.spi.transfer(transmitted_data_bytes)

        assert isinstance(received_data_bytes, list)

        parsed_data_bytes = []
        begin = 0

        for command in commands:
            end = begin + len(command.transmitted_data_bytes)

            parsed_data_bytes.append(
                command.parse_received_data_bytes(
                    received_data_bytes[begin:end],
                ),
            )

            begin = end

        return parsed_data_bytes

    def read(self, memory_address: int) -> int:
        """Read the data at the memory address.

        :param memory_address: The memory address.
        :return: The read data.
        """
        datum = self.command(Read(memory_address))[0]

        assert datum is not None

        return datum

    def write(self, memory_address: int, data: int) -> None:
        """Write the data at the memory address.

        :param memory_address: The memory address.
        :param data: The data.
        :return: ``None``.
        """
        self.command(Write(memory_address, data))

    def increment(self, memory_address: int) -> None:
        """Increment the data at the memory address.

        :param memory_address: The memory address.
        :return: ``None``.
        """
        self.command(Increment(memory_address))

    def decrement(self, memory_address: int) -> None:
        """Decrement the data at the memory address.

        :param memory_address: The memory address.
        :return: ``None``.
        """
        self.command(Decrement(memory_address))

    def set_volatile_wiper_step(self, step: int) -> None:
        """Set the volatile wiper step.

        :param step: The step.
        :return: ``None``.
        """
        if step not in self.STEP_RANGE:
            raise ValueError('invalid step')

        self.write(MemoryAddress.VOLATILE_WIPER_0, step)

    def set_non_volatile_wiper_step(self, step: int) -> None:
        """Set the non-volatile wiper step.

        :param step: The step.
        :return: ``None``.
        """
        if step not in self.STEP_RANGE:
            raise ValueError('invalid step')

        self.write(MemoryAddress.NON_VOLATILE_WIPER_0, step)

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar
from warnings import warn

from periphery import SPI


@dataclass
class MCP4161:
    """A Python driver for Microchip Technology MCP4161 7/8-Bit
    Single/Dual SPI Digital POT with Non-Volatile Memory
    """

    class MemoryAddress(IntEnum):
        """The enum class for memory addresses."""

        VOLATILE_WIPER_0: int = 0x00
        """The volatile wiper 0."""
        NON_VOLATILE_WIPER_0: int = 0x02
        """The non-volatile wiper 0."""
        VOLATILE_TCON_REGISTER: int = 0x04
        """The volatile TCON register."""
        STATUS_REGISTER: int = 0x05
        """The status register."""

    @dataclass
    class Command(ABC):
        """The abstract base class class for commands."""

        COMMAND_BITS: ClassVar[int]
        """The command bits."""
        memory_address: int
        """The memory address."""

        @property
        @abstractmethod
        def transmitted_data(self) -> list[int]:
            pass

        @abstractmethod
        def parse(self, received_data: list[int]) -> int | None:
            pass

    @dataclass
    class SixteenBitCommand(Command, ABC):
        """The abstract base class for 8-bit commands."""

        pass

    @dataclass
    class ReadData(SixteenBitCommand):
        """The class for read data commands."""

        COMMAND_BITS: ClassVar[int] = 0b11

        @property
        def transmitted_data(self) -> list[int]:
            return [
                (
                    (self.memory_address << MCP4161.MEMORY_ADDRESS_OFFSET)
                    | (self.COMMAND_BITS << MCP4161.COMMAND_BITS_OFFSET)
                    | ((1 << MCP4161.COMMAND_BITS_OFFSET) - 1)
                ),
                (1 << MCP4161.SPI_WORD_BIT_COUNT) - 1,
            ]

        def parse(self, received_data: list[int]) -> int:
            return (
                (
                    (received_data[0] << MCP4161.SPI_WORD_BIT_COUNT)
                    | received_data[1]
                )
                & ((1 << MCP4161.DATA_BIT_COUNT) - 1)
            )

    @dataclass
    class WriteData(SixteenBitCommand):
        """The class for read data commands."""

        COMMAND_BITS: ClassVar[int] = 0b00
        data: int
        """The data."""

        @property
        def transmitted_data(self) -> list[int]:
            return [
                (
                    (self.memory_address << MCP4161.MEMORY_ADDRESS_OFFSET)
                    | (self.COMMAND_BITS << MCP4161.COMMAND_BITS_OFFSET)
                    | (self.data >> MCP4161.SPI_WORD_BIT_COUNT)
                ),
                self.data & ((1 << MCP4161.SPI_WORD_BIT_COUNT) - 1),
            ]

        def parse(self, received_data: list[int]) -> None:
            return None

    @dataclass
    class EightBitCommand(Command, ABC):
        """The abstract base class for 8-bit commands."""

        @property
        def transmitted_data(self) -> list[int]:
            return [
                (self.memory_address << MCP4161.MEMORY_ADDRESS_OFFSET)
                | (self.COMMAND_BITS << MCP4161.COMMAND_BITS_OFFSET),
            ]

    @dataclass
    class Increment(EightBitCommand):
        """The class for increment commands."""

        COMMAND_BITS: ClassVar[int] = 0b01

        def parse(self, received_data: list[int]) -> None:
            return None

    @dataclass
    class Decrement(EightBitCommand):
        """The class for decrement commands."""

        COMMAND_BITS: ClassVar[int] = 0b10

        def parse(self, received_data: list[int]) -> None:
            return None

    SPI_MODES: ClassVar[tuple[int, int]] = 0b00, 0b11
    """The supported spi modes."""
    MAX_SPI_MAX_SPEED: ClassVar[float] = 10e6
    """The supported maximum spi maximum speed."""
    SPI_BIT_ORDER: ClassVar[str] = 'msb'
    """The supported spi bit order."""
    SPI_WORD_BIT_COUNT: ClassVar[int] = 8
    """The supported spi number of bits per word."""
    MEMORY_ADDRESS_OFFSET: ClassVar[int] = 4
    """The memory address offset for the command byte."""
    COMMAND_BITS_OFFSET: ClassVar[int] = 2
    """The command bits offset for the command byte."""
    DATA_BIT_COUNT: ClassVar[int] = 9
    """The supported number of data bits."""
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

    def command(self, *commands: Command) -> list[int | None]:
        transmitted_data = []

        for command in commands:
            transmitted_data.extend(command.transmitted_data)

        received_data = self.spi.transfer(transmitted_data)

        assert isinstance(received_data, list)

        parsed_data = []
        begin = 0

        for command in commands:
            end = begin + len(command.transmitted_data)

            parsed_data.append(command.parse(received_data[begin:end]))

            begin = end

        return parsed_data

    def read_data(self, memory_address: int) -> int:
        """Read the data at the memory address.

        :param memory_address: The memory address.
        :return: The read data.
        """
        datum = self.command(self.ReadData(memory_address))[0]

        assert datum is not None

        return datum

    def write_data(self, memory_address: int, data: int) -> None:
        """Write the data at the memory address.

        :param memory_address: The memory address.
        :param data: The data.
        :return: ``None``.
        """
        self.command(self.WriteData(memory_address, data))

    def increment(self, memory_address: int) -> None:
        """Increment the data at the memory address.

        :param memory_address: The memory address.
        :return: ``None``.
        """
        self.command(self.Increment(memory_address))

    def decrement(self, memory_address: int) -> None:
        """Decrement the data at the memory address.

        :param memory_address: The memory address.
        :return: ``None``.
        """
        self.command(self.Decrement(memory_address))

    def set_step(self, step: int, eeprom: bool = False) -> None:
        """Set the volatile or non-volatile wiper step.

        :param step: The step.
        :param eeprom: ``True`` if non-volatile, otherwise ``False``.
        :return: ``None``.
        """
        if eeprom:
            memory_address = self.MemoryAddress.NON_VOLATILE_WIPER_0
        else:
            memory_address = self.MemoryAddress.VOLATILE_WIPER_0

        if step not in self.STEP_RANGE:
            raise ValueError('invalid step')

        self.write_data(memory_address, step)

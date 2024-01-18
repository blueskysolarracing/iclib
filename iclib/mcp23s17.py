from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import auto, Enum, IntEnum
from typing import cast, ClassVar
from warnings import warn

from periphery import GPIO, SPI


@dataclass
class MCP23S17:
    """A Python driver for Microchip Technology MCP23S17 16-Bit I/O
    Expander with Serial Interface
    """

    class Port(IntEnum):
        """The enum class for ports."""

        PORTA = auto()
        """PORTA."""
        PORTB = auto()
        """PORTB."""

    class Mode(IntEnum):
        """The enum class for modes."""

        EIGHT_BIT_MODE = auto()
        """8-bit mode."""
        SIXTEEN_BIT_MODE = auto()
        """16-bit mode."""

    class Register(Enum):
        _ignore_ = '_Register'

        class _Register(ABC):
            BITS: ClassVar[type[IntEnum]]
            ADDRESS: ClassVar[int]

        class IODIR(_Register):
            class IO(IntEnum):
                IO0 = 0
                IO1 = 1
                IO2 = 2
                IO3 = 3
                IO4 = 4
                IO5 = 5
                IO6 = 6
                IO7 = 7

            BITS = IO
            ADDRESS: ClassVar[int] = 0x00

        class IPOL(_Register):
            class IP(IntEnum):
                IP0 = 0
                IP1 = 1
                IP2 = 2
                IP3 = 3
                IP4 = 4
                IP5 = 5
                IP6 = 6
                IP7 = 7

            BITS = IP
            ADDRESS: ClassVar[int] = 0x01

        class GPINTEN(_Register):
            class GPINT(IntEnum):
                GPINT0 = 0
                GPINT1 = 1
                GPINT2 = 2
                GPINT3 = 3
                GPINT4 = 4
                GPINT5 = 5
                GPINT6 = 6
                GPINT7 = 7

            BITS = GPINT
            ADDRESS: ClassVar[int] = 0x02

        class DEFVAL(_Register):
            class DEF(IntEnum):
                DEF0 = 0
                DEF1 = 1
                DEF2 = 2
                DEF3 = 3
                DEF4 = 4
                DEF5 = 5
                DEF6 = 6
                DEF7 = 7

            BITS = DEF
            ADDRESS: ClassVar[int] = 0x03

        class INTCON(_Register):
            class IOC(IntEnum):
                IOC0 = 0
                IOC1 = 1
                IOC2 = 2
                IOC3 = 3
                IOC4 = 4
                IOC5 = 5
                IOC6 = 6
                IOC7 = 7

            BITS = IOC
            ADDRESS: ClassVar[int] = 0x04

        class IOCON(_Register):
            class BITS(IntEnum):
                UNIMPLEMENTED = 0
                INTPOL = 1
                ODR = 2
                HAEN = 3
                DISSLW = 4
                SEQOP = 5
                MIRROR = 6
                BANK = 7

            ADDRESS: ClassVar[int] = 0x05

        class GPPU(_Register):
            class PU(IntEnum):
                PU0 = 0
                PU1 = 1
                PU2 = 2
                PU3 = 3
                PU4 = 4
                PU5 = 5
                PU6 = 6
                PU7 = 7

            BITS = PU
            ADDRESS: ClassVar[int] = 0x06

        class INTF(_Register):
            class INT(IntEnum):
                INT0 = 0
                INT1 = 1
                INT2 = 2
                INT3 = 3
                INT4 = 4
                INT5 = 5
                INT6 = 6
                INT7 = 7

            BITS = INT
            ADDRESS: ClassVar[int] = 0x07

        class INTCAP(_Register):
            class ICP(IntEnum):
                ICP0 = 0
                ICP1 = 1
                ICP2 = 2
                ICP3 = 3
                ICP4 = 4
                ICP5 = 5
                ICP6 = 6
                ICP7 = 7

            BITS = ICP
            ADDRESS: ClassVar[int] = 0x08

        class GPIO(_Register):
            class GP(IntEnum):
                GP0 = 0
                GP1 = 1
                GP2 = 2
                GP3 = 3
                GP4 = 4
                GP5 = 5
                GP6 = 6
                GP7 = 7

            BITS = GP
            ADDRESS: ClassVar[int] = 0x09

        class OLAT(_Register):
            class OL(IntEnum):
                OL0 = 0
                OL1 = 1
                OL2 = 2
                OL3 = 3
                OL4 = 4
                OL5 = 5
                OL6 = 6
                OL7 = 7

            BITS = OL
            ADDRESS: ClassVar[int] = 0x0A

        @property
        def bits(self) -> type[IntEnum]:
            return cast(type[IntEnum], self.value.BITS)

        @property
        def address(self) -> int:
            return cast(int, self.value.ADDRESS)

    @dataclass
    class Operation(ABC):
        READ_OR_WRITE_BIT: ClassVar[int]
        hardware_address: int
        register_address: int

        @property
        def control_byte(self) -> int:
            return (
                (MCP23S17.FIXED_BITS << MCP23S17.FIXED_BITS_OFFSET)
                | (self.hardware_address << MCP23S17.CLIENT_ADDRESS_OFFSET)
                | (self.READ_OR_WRITE_BIT << MCP23S17.READ_OR_WRITE_BIT_OFFSET)
            )

        @property
        @abstractmethod
        def data_bytes(self) -> list[int]:
            pass

        @property
        def transmitted_data(self) -> list[int]:
            return [self.control_byte, self.register_address, *self.data_bytes]

        @abstractmethod
        def parse(self, received_data: list[int]) -> list[int] | None:
            pass

    @dataclass
    class Read(Operation):
        READ_OR_WRITE_BIT: ClassVar[int] = 1
        data_byte_count: int

        @property
        def data_bytes(self) -> list[int]:
            return (
                [(1 << MCP23S17.SPI_WORD_BIT_COUNT) - 1] * self.data_byte_count
            )

        def parse(self, received_data: list[int]) -> list[int]:
            return received_data[-self.data_byte_count:]

    @dataclass
    class Write(Operation):
        READ_OR_WRITE_BIT: ClassVar[int] = 0
        data_bytes: list[int]

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
    FIXED_BITS: ClassVar[int] = 0b0100
    """The four fixed bits."""
    FIXED_BITS_OFFSET: ClassVar[int] = 4
    """The fixed-bits offset."""
    CLIENT_ADDRESS_OFFSET: ClassVar[int] = 1
    """The client address offset."""
    READ_OR_WRITE_BIT_OFFSET: ClassVar[int] = 0
    """The R/W bit offset."""
    hardware_reset_gpio: GPIO
    """The hardware reset GPIO."""
    interrupt_output_a_gpio: GPIO
    """The interrupt output for PORTA GPIO."""
    interrupt_output_b_gpio: GPIO
    """The interrupt output for PORTB GPIO."""
    spi: SPI
    """The SPI."""
    callback: Callable[[Port], None]
    """The callback function."""

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

    def operate(self, *operations: Operation) -> list[list[int] | None]:
        transmitted_data = []

        for operation in operations:
            transmitted_data.extend(operation.transmitted_data)

        received_data = self.spi.transfer(transmitted_data)

        assert isinstance(received_data, list)

        parsed_data = []
        begin = 0

        for operation in operations:
            end = begin + len(operation.transmitted_data)

            parsed_data.append(operation.parse(received_data[begin:end]))

            begin = end

        return parsed_data

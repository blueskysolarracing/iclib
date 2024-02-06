"""This module implements the MCP23S17 driver."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import auto, Enum, IntEnum
from typing import ClassVar
from warnings import warn

from periphery import GPIO, SPI

SPI_MODES: tuple[int, int] = 0b00, 0b11
"""The supported spi modes."""
MAX_SPI_MAX_SPEED: float = 10e6
"""The supported maximum spi maximum speed."""
SPI_BIT_ORDER: str = 'msb'
"""The supported spi bit order."""
SPI_WORD_BIT_COUNT: int = 8
"""The supported spi number of bits per word."""


class Port(Enum):
    """The enum class for ports."""

    PORTA = auto()
    """PORTA."""
    PORTB = auto()
    """PORTB."""


class Mode(IntEnum):
    """The enum class for modes."""

    SIXTEEN_BIT_MODE = auto()
    """16-bit mode."""
    EIGHT_BIT_MODE = auto()
    """8-bit mode."""


class RegisterBit(Enum):
    IODIR = 0x00
    IODIR_IO0 = 0x00, 0
    IODIR_IO1 = 0x00, 1
    IODIR_IO2 = 0x00, 2
    IODIR_IO3 = 0x00, 3
    IODIR_IO4 = 0x00, 4
    IODIR_IO5 = 0x00, 5
    IODIR_IO6 = 0x00, 6
    IODIR_IO7 = 0x00, 7

    IPOL = 0x01
    IPOL_IP0 = 0x01, 0
    IPOL_IP1 = 0x01, 1
    IPOL_IP2 = 0x01, 2
    IPOL_IP3 = 0x01, 3
    IPOL_IP4 = 0x01, 4
    IPOL_IP5 = 0x01, 5
    IPOL_IP6 = 0x01, 6
    IPOL_IP7 = 0x01, 7

    GPINTEN = 0x02
    GPINTEN_GPINT0 = 0x02, 0
    GPINTEN_GPINT1 = 0x02, 1
    GPINTEN_GPINT2 = 0x02, 2
    GPINTEN_GPINT3 = 0x02, 3
    GPINTEN_GPINT4 = 0x02, 4
    GPINTEN_GPINT5 = 0x02, 5
    GPINTEN_GPINT6 = 0x02, 6
    GPINTEN_GPINT7 = 0x02, 7

    DEFVAL = 0x03
    DEFVAL_DEF0 = 0x03, 0
    DEFVAL_DEF1 = 0x03, 1
    DEFVAL_DEF2 = 0x03, 2
    DEFVAL_DEF3 = 0x03, 3
    DEFVAL_DEF4 = 0x03, 4
    DEFVAL_DEF5 = 0x03, 5
    DEFVAL_DEF6 = 0x03, 6
    DEFVAL_DEF7 = 0x03, 7

    INTCON = 0x04
    INTCON_IOC0 = 0x04, 0
    INTCON_IOC1 = 0x04, 1
    INTCON_IOC2 = 0x04, 2
    INTCON_IOC3 = 0x04, 3
    INTCON_IOC4 = 0x04, 4
    INTCON_IOC5 = 0x04, 5
    INTCON_IOC6 = 0x04, 6
    INTCON_IOC7 = 0x04, 7

    IOCON = 0x05
    IOCON_UNIMPLEMENTED = 0x05, 0
    IOCON_INTPOL = 0x05, 1
    IOCON_ODR = 0x05, 2
    IOCON_HAEN = 0x05, 3
    IOCON_DISSLW = 0x05, 4
    IOCON_SEQOP = 0x05, 5
    IOCON_MIRROR = 0x05, 6
    IOCON_BANK = 0x05, 7

    GPPU = 0x06
    GPPU_PU0 = 0x06, 0
    GPPU_PU1 = 0x06, 1
    GPPU_PU2 = 0x06, 2
    GPPU_PU3 = 0x06, 3
    GPPU_PU4 = 0x06, 4
    GPPU_PU5 = 0x06, 5
    GPPU_PU6 = 0x06, 6
    GPPU_PU7 = 0x06, 7

    INTF = 0x07
    INTF_INT0 = 0x07, 0
    INTF_INT1 = 0x07, 1
    INTF_INT2 = 0x07, 2
    INTF_INT3 = 0x07, 3
    INTF_INT4 = 0x07, 4
    INTF_INT5 = 0x07, 5
    INTF_INT6 = 0x07, 6
    INTF_INT7 = 0x07, 7

    INTCAP = 0x08
    INTCAP_ICP0 = 0x08, 0
    INTCAP_ICP1 = 0x08, 1
    INTCAP_ICP2 = 0x08, 2
    INTCAP_ICP3 = 0x08, 3
    INTCAP_ICP4 = 0x08, 4
    INTCAP_ICP5 = 0x08, 5
    INTCAP_ICP6 = 0x08, 6
    INTCAP_ICP7 = 0x08, 7

    GPIO = 0x09
    GPIO_GP0 = 0x09, 0
    GPIO_GP1 = 0x09, 1
    GPIO_GP2 = 0x09, 2
    GPIO_GP3 = 0x09, 3
    GPIO_GP4 = 0x09, 4
    GPIO_GP5 = 0x09, 5
    GPIO_GP6 = 0x09, 6
    GPIO_GP7 = 0x09, 7

    OLAT = 0x0A
    OLAT_OL0 = 0x0A, 0
    OLAT_OL1 = 0x0A, 1
    OLAT_OL2 = 0x0A, 2
    OLAT_OL3 = 0x0A, 3
    OLAT_OL4 = 0x0A, 4
    OLAT_OL5 = 0x0A, 5
    OLAT_OL6 = 0x0A, 6
    OLAT_OL7 = 0x0A, 7


@dataclass
class Operation(ABC):
    READ_OR_WRITE_BIT: ClassVar[int]
    hardware_address: int
    register_address: int

    @property
    def control_byte(self) -> int:
        return (
            (0b0100 << 4)
            | (self.hardware_address << 1)
            | self.READ_OR_WRITE_BIT
        )

    @property
    @abstractmethod
    def data_bytes(self) -> list[int]:
        pass

    @property
    @abstractmethod
    def data_byte_count(self) -> int:
        pass

    @property
    def transmitted_data_bytes(self) -> list[int]:
        return [self.control_byte, self.register_address, *self.data_bytes]

    @property
    def transmitted_data_byte_count(self) -> int:
        return 2 + self.data_byte_count

    def parse_received_data_bytes(
            self,
            data_bytes: list[int],
    ) -> list[int]:
        return data_bytes[-self.data_byte_count:]


@dataclass
class Read(Operation):
    READ_OR_WRITE_BIT: ClassVar[int] = 1
    data_byte_count: int

    @property
    def data_bytes(self) -> list[int]:
        return [(1 << SPI_WORD_BIT_COUNT) - 1] * self.data_byte_count


@dataclass
class Write(Operation):
    READ_OR_WRITE_BIT: ClassVar[int] = 0
    data_bytes: list[int]

    @property
    def data_byte_count(self) -> int:
        return len(self.data_bytes)


@dataclass
class MCP23S17:
    """A Python driver for Microchip Technology MCP23S17 16-Bit I/O
    Expander with Serial Interface
    """

    hardware_reset_gpio: GPIO
    """The hardware reset GPIO."""
    interrupt_output_a_gpio: GPIO
    """The interrupt output for PORTA GPIO."""
    interrupt_output_b_gpio: GPIO
    """The interrupt output for PORTB GPIO."""
    spi: SPI
    """The SPI."""
    hardware_address: int = 0
    """The hardware address."""
    # callback: Callable[[Port], None]
    # """The callback function."""

    def __post_init__(self) -> None:
        if self.spi.mode not in SPI_MODES:
            raise ValueError('unsupported spi mode')
        elif self.spi.max_speed > MAX_SPI_MAX_SPEED:
            raise ValueError('unsupported spi maximum speed')
        elif self.spi.bit_order != SPI_BIT_ORDER:
            raise ValueError('unsupported spi bit order')
        elif self.spi.bits_per_word != SPI_WORD_BIT_COUNT:
            raise ValueError('unsupported spi number of bits per word')

        if self.spi.extra_flags:
            warn(f'unknown spi extra flags {self.spi.extra_flags}')

    def operate(self, *operations: Operation) -> list[int]:
        transmitted_data_bytes = []

        for operation in operations:
            transmitted_data_bytes.extend(operation.transmitted_data_bytes)

        received_data_bytes = self.spi.transfer(transmitted_data_bytes)

        assert isinstance(received_data_bytes, list)

        parsed_received_data_bytes = []
        begin = 0

        for operation in operations:
            end = begin + operation.transmitted_data_byte_count

            parsed_received_data_bytes.extend(
                operation.parse_received_data_bytes(
                    received_data_bytes[begin:end],
                ),
            )

            begin = end

        return parsed_received_data_bytes

    def read_raw(
            self,
            register_address: int,
            data_byte_count: int,
    ) -> list[int]:
        return self.operate(
            Read(self.hardware_address, register_address, data_byte_count),
        )

    def write_raw(
            self,
            register_address: int,
            data_bytes: list[int],
    ) -> list[int]:
        return self.operate(
            Write(self.hardware_address, register_address, data_bytes),
        )

    def read(
            self,
            port: Port,
            register: int,
            data_byte_count: int = 1,
    ) -> list[int]:
        register_address = 0  # TODO
        return self.read_raw(register_address, data_byte_count)

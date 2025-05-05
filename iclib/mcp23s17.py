"""This module implements the MCP23S17 driver."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import auto, Enum, IntEnum
from typing import ClassVar
from warnings import warn

from periphery import GPIO, SPI


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


class Register(IntEnum):
    IODIR = 0x00
    IPOL = 0x01
    GPINTEN = 0x02
    DEFVAL = 0x03
    INTCON = 0x04
    IOCON = 0x05
    GPPU = 0x06
    INTF = 0x07
    INTCAP = 0x08
    GPIO = 0x09
    OLAT = 0x0A


class RegisterBit(tuple[Register, int], Enum):
    IODIR_IO0 = Register.IODIR, 0
    IODIR_IO1 = Register.IODIR, 1
    IODIR_IO2 = Register.IODIR, 2
    IODIR_IO3 = Register.IODIR, 3
    IODIR_IO4 = Register.IODIR, 4
    IODIR_IO5 = Register.IODIR, 5
    IODIR_IO6 = Register.IODIR, 6
    IODIR_IO7 = Register.IODIR, 7

    IPOL_IP0 = Register.IPOL, 0
    IPOL_IP1 = Register.IPOL, 1
    IPOL_IP2 = Register.IPOL, 2
    IPOL_IP3 = Register.IPOL, 3
    IPOL_IP4 = Register.IPOL, 4
    IPOL_IP5 = Register.IPOL, 5
    IPOL_IP6 = Register.IPOL, 6
    IPOL_IP7 = Register.IPOL, 7

    GPINTEN_GPINT0 = Register.GPINTEN, 0
    GPINTEN_GPINT1 = Register.GPINTEN, 1
    GPINTEN_GPINT2 = Register.GPINTEN, 2
    GPINTEN_GPINT3 = Register.GPINTEN, 3
    GPINTEN_GPINT4 = Register.GPINTEN, 4
    GPINTEN_GPINT5 = Register.GPINTEN, 5
    GPINTEN_GPINT6 = Register.GPINTEN, 6
    GPINTEN_GPINT7 = Register.GPINTEN, 7

    DEFVAL_DEF0 = Register.DEFVAL, 0
    DEFVAL_DEF1 = Register.DEFVAL, 1
    DEFVAL_DEF2 = Register.DEFVAL, 2
    DEFVAL_DEF3 = Register.DEFVAL, 3
    DEFVAL_DEF4 = Register.DEFVAL, 4
    DEFVAL_DEF5 = Register.DEFVAL, 5
    DEFVAL_DEF6 = Register.DEFVAL, 6
    DEFVAL_DEF7 = Register.DEFVAL, 7

    INTCON_IOC0 = Register.INTCON, 0
    INTCON_IOC1 = Register.INTCON, 1
    INTCON_IOC2 = Register.INTCON, 2
    INTCON_IOC3 = Register.INTCON, 3
    INTCON_IOC4 = Register.INTCON, 4
    INTCON_IOC5 = Register.INTCON, 5
    INTCON_IOC6 = Register.INTCON, 6
    INTCON_IOC7 = Register.INTCON, 7

    IOCON_UNIMPLEMENTED = Register.IOCON, 0
    IOCON_INTPOL = Register.IOCON, 1
    IOCON_ODR = Register.IOCON, 2
    IOCON_HAEN = Register.IOCON, 3
    IOCON_DISSLW = Register.IOCON, 4
    IOCON_SEQOP = Register.IOCON, 5
    IOCON_MIRROR = Register.IOCON, 6
    IOCON_BANK = Register.IOCON, 7

    GPPU_PU0 = Register.GPPU, 0
    GPPU_PU1 = Register.GPPU, 1
    GPPU_PU2 = Register.GPPU, 2
    GPPU_PU3 = Register.GPPU, 3
    GPPU_PU4 = Register.GPPU, 4
    GPPU_PU5 = Register.GPPU, 5
    GPPU_PU6 = Register.GPPU, 6
    GPPU_PU7 = Register.GPPU, 7

    INTF_INT0 = Register.INTF, 0
    INTF_INT1 = Register.INTF, 1
    INTF_INT2 = Register.INTF, 2
    INTF_INT3 = Register.INTF, 3
    INTF_INT4 = Register.INTF, 4
    INTF_INT5 = Register.INTF, 5
    INTF_INT6 = Register.INTF, 6
    INTF_INT7 = Register.INTF, 7

    INTCAP_ICP0 = Register.INTCAP, 0
    INTCAP_ICP1 = Register.INTCAP, 1
    INTCAP_ICP2 = Register.INTCAP, 2
    INTCAP_ICP3 = Register.INTCAP, 3
    INTCAP_ICP4 = Register.INTCAP, 4
    INTCAP_ICP5 = Register.INTCAP, 5
    INTCAP_ICP6 = Register.INTCAP, 6
    INTCAP_ICP7 = Register.INTCAP, 7

    GPIO_GP0 = Register.GPIO, 0
    GPIO_GP1 = Register.GPIO, 1
    GPIO_GP2 = Register.GPIO, 2
    GPIO_GP3 = Register.GPIO, 3
    GPIO_GP4 = Register.GPIO, 4
    GPIO_GP5 = Register.GPIO, 5
    GPIO_GP6 = Register.GPIO, 6
    GPIO_GP7 = Register.GPIO, 7

    OLAT_OL0 = Register.OLAT, 0
    OLAT_OL1 = Register.OLAT, 1
    OLAT_OL2 = Register.OLAT, 2
    OLAT_OL3 = Register.OLAT, 3
    OLAT_OL4 = Register.OLAT, 4
    OLAT_OL5 = Register.OLAT, 5
    OLAT_OL6 = Register.OLAT, 6
    OLAT_OL7 = Register.OLAT, 7


class PortRegister(tuple[Port, Register], Enum):
    IODIRA = Port.PORTA, Register.IODIR
    IODIRB = Port.PORTB, Register.IODIR
    IPOLA = Port.PORTA, Register.IPOL
    IPOLB = Port.PORTB, Register.IPOL
    GPINTENA = Port.PORTA, Register.GPINTEN
    GPINTENB = Port.PORTB, Register.GPINTEN
    DEFVALA = Port.PORTA, Register.DEFVAL
    DEFVALB = Port.PORTB, Register.DEFVAL
    INTCONA = Port.PORTA, Register.INTCON
    INTCONB = Port.PORTB, Register.INTCON
    IOCONA = Port.PORTA, Register.IOCON
    IOCONB = Port.PORTB, Register.IOCON
    GPPUA = Port.PORTA, Register.GPPU
    GPPUB = Port.PORTB, Register.GPPU
    INTFA = Port.PORTA, Register.INTF
    INTFB = Port.PORTB, Register.INTF
    INTCAPA = Port.PORTA, Register.INTCAP
    INTCAPB = Port.PORTB, Register.INTCAP
    GPIOA = Port.PORTA, Register.GPIO
    GPIOB = Port.PORTB, Register.GPIO
    OLATA = Port.PORTA, Register.OLAT
    OLATB = Port.PORTB, Register.OLAT


class PortRegisterBit(tuple[Port, Register, int], Enum):
    IODIRA_IO0 = Port.PORTA, *RegisterBit.IODIR_IO0
    IODIRB_IO0 = Port.PORTB, *RegisterBit.IODIR_IO0
    IODIRA_IO1 = Port.PORTA, *RegisterBit.IODIR_IO1
    IODIRB_IO1 = Port.PORTB, *RegisterBit.IODIR_IO1
    IODIRA_IO2 = Port.PORTA, *RegisterBit.IODIR_IO2
    IODIRB_IO2 = Port.PORTB, *RegisterBit.IODIR_IO2
    IODIRA_IO3 = Port.PORTA, *RegisterBit.IODIR_IO3
    IODIRB_IO3 = Port.PORTB, *RegisterBit.IODIR_IO3
    IODIRA_IO4 = Port.PORTA, *RegisterBit.IODIR_IO4
    IODIRB_IO4 = Port.PORTB, *RegisterBit.IODIR_IO4
    IODIRA_IO5 = Port.PORTA, *RegisterBit.IODIR_IO5
    IODIRB_IO5 = Port.PORTB, *RegisterBit.IODIR_IO5
    IODIRA_IO6 = Port.PORTA, *RegisterBit.IODIR_IO6
    IODIRB_IO6 = Port.PORTB, *RegisterBit.IODIR_IO6
    IODIRA_IO7 = Port.PORTA, *RegisterBit.IODIR_IO7
    IODIRB_IO7 = Port.PORTB, *RegisterBit.IODIR_IO7

    IPOLA_IP0 = Port.PORTA, *RegisterBit.IPOL_IP0
    IPOLB_IP0 = Port.PORTB, *RegisterBit.IPOL_IP0
    IPOLA_IP1 = Port.PORTA, *RegisterBit.IPOL_IP1
    IPOLB_IP1 = Port.PORTB, *RegisterBit.IPOL_IP1
    IPOLA_IP2 = Port.PORTA, *RegisterBit.IPOL_IP2
    IPOLB_IP2 = Port.PORTB, *RegisterBit.IPOL_IP2
    IPOLA_IP3 = Port.PORTA, *RegisterBit.IPOL_IP3
    IPOLB_IP3 = Port.PORTB, *RegisterBit.IPOL_IP3
    IPOLA_IP4 = Port.PORTA, *RegisterBit.IPOL_IP4
    IPOLB_IP4 = Port.PORTB, *RegisterBit.IPOL_IP4
    IPOLA_IP5 = Port.PORTA, *RegisterBit.IPOL_IP5
    IPOLB_IP5 = Port.PORTB, *RegisterBit.IPOL_IP5
    IPOLA_IP6 = Port.PORTA, *RegisterBit.IPOL_IP6
    IPOLB_IP6 = Port.PORTB, *RegisterBit.IPOL_IP6
    IPOLA_IP7 = Port.PORTA, *RegisterBit.IPOL_IP7
    IPOLB_IP7 = Port.PORTB, *RegisterBit.IPOL_IP7

    GPINTENA_GPINT0 = Port.PORTA, *RegisterBit.GPINTEN_GPINT0
    GPINTENB_GPINT0 = Port.PORTB, *RegisterBit.GPINTEN_GPINT0
    GPINTENA_GPINT1 = Port.PORTA, *RegisterBit.GPINTEN_GPINT1
    GPINTENB_GPINT1 = Port.PORTB, *RegisterBit.GPINTEN_GPINT1
    GPINTENA_GPINT2 = Port.PORTA, *RegisterBit.GPINTEN_GPINT2
    GPINTENB_GPINT2 = Port.PORTB, *RegisterBit.GPINTEN_GPINT2
    GPINTENA_GPINT3 = Port.PORTA, *RegisterBit.GPINTEN_GPINT3
    GPINTENB_GPINT3 = Port.PORTB, *RegisterBit.GPINTEN_GPINT3
    GPINTENA_GPINT4 = Port.PORTA, *RegisterBit.GPINTEN_GPINT4
    GPINTENB_GPINT4 = Port.PORTB, *RegisterBit.GPINTEN_GPINT4
    GPINTENA_GPINT5 = Port.PORTA, *RegisterBit.GPINTEN_GPINT5
    GPINTENB_GPINT5 = Port.PORTB, *RegisterBit.GPINTEN_GPINT5
    GPINTENA_GPINT6 = Port.PORTA, *RegisterBit.GPINTEN_GPINT6
    GPINTENB_GPINT6 = Port.PORTB, *RegisterBit.GPINTEN_GPINT6
    GPINTENA_GPINT7 = Port.PORTA, *RegisterBit.GPINTEN_GPINT7
    GPINTENB_GPINT7 = Port.PORTB, *RegisterBit.GPINTEN_GPINT7

    DEFVALA_DEF0 = Port.PORTA, *RegisterBit.DEFVAL_DEF0
    DEFVALB_DEF0 = Port.PORTB, *RegisterBit.DEFVAL_DEF0
    DEFVALA_DEF1 = Port.PORTA, *RegisterBit.DEFVAL_DEF1
    DEFVALB_DEF1 = Port.PORTB, *RegisterBit.DEFVAL_DEF1
    DEFVALA_DEF2 = Port.PORTA, *RegisterBit.DEFVAL_DEF2
    DEFVALB_DEF2 = Port.PORTB, *RegisterBit.DEFVAL_DEF2
    DEFVALA_DEF3 = Port.PORTA, *RegisterBit.DEFVAL_DEF3
    DEFVALB_DEF3 = Port.PORTB, *RegisterBit.DEFVAL_DEF3
    DEFVALA_DEF4 = Port.PORTA, *RegisterBit.DEFVAL_DEF4
    DEFVALB_DEF4 = Port.PORTB, *RegisterBit.DEFVAL_DEF4
    DEFVALA_DEF5 = Port.PORTA, *RegisterBit.DEFVAL_DEF5
    DEFVALB_DEF5 = Port.PORTB, *RegisterBit.DEFVAL_DEF5
    DEFVALA_DEF6 = Port.PORTA, *RegisterBit.DEFVAL_DEF6
    DEFVALB_DEF6 = Port.PORTB, *RegisterBit.DEFVAL_DEF6
    DEFVALA_DEF7 = Port.PORTA, *RegisterBit.DEFVAL_DEF7
    DEFVALB_DEF7 = Port.PORTB, *RegisterBit.DEFVAL_DEF7

    INTCONA_IOC0 = Port.PORTA, *RegisterBit.INTCON_IOC0
    INTCONB_IOC0 = Port.PORTB, *RegisterBit.INTCON_IOC0
    INTCONA_IOC1 = Port.PORTA, *RegisterBit.INTCON_IOC1
    INTCONB_IOC1 = Port.PORTB, *RegisterBit.INTCON_IOC1
    INTCONA_IOC2 = Port.PORTA, *RegisterBit.INTCON_IOC2
    INTCONB_IOC2 = Port.PORTB, *RegisterBit.INTCON_IOC2
    INTCONA_IOC3 = Port.PORTA, *RegisterBit.INTCON_IOC3
    INTCONB_IOC3 = Port.PORTB, *RegisterBit.INTCON_IOC3
    INTCONA_IOC4 = Port.PORTA, *RegisterBit.INTCON_IOC4
    INTCONB_IOC4 = Port.PORTB, *RegisterBit.INTCON_IOC4
    INTCONA_IOC5 = Port.PORTA, *RegisterBit.INTCON_IOC5
    INTCONB_IOC5 = Port.PORTB, *RegisterBit.INTCON_IOC5
    INTCONA_IOC6 = Port.PORTA, *RegisterBit.INTCON_IOC6
    INTCONB_IOC6 = Port.PORTB, *RegisterBit.INTCON_IOC6
    INTCONA_IOC7 = Port.PORTA, *RegisterBit.INTCON_IOC7
    INTCONB_IOC7 = Port.PORTB, *RegisterBit.INTCON_IOC7

    IOCONA_UNIMPLEMENTED = Port.PORTA, *RegisterBit.IOCON_UNIMPLEMENTED
    IOCONB_UNIMPLEMENTED = Port.PORTB, *RegisterBit.IOCON_UNIMPLEMENTED
    IOCONA_INTPOL = Port.PORTA, *RegisterBit.IOCON_INTPOL
    IOCONB_INTPOL = Port.PORTB, *RegisterBit.IOCON_INTPOL
    IOCONA_ODR = Port.PORTA, *RegisterBit.IOCON_ODR
    IOCONB_ODR = Port.PORTB, *RegisterBit.IOCON_ODR
    IOCONA_HAEN = Port.PORTA, *RegisterBit.IOCON_HAEN
    IOCONB_HAEN = Port.PORTB, *RegisterBit.IOCON_HAEN
    IOCONA_DISSLW = Port.PORTA, *RegisterBit.IOCON_DISSLW
    IOCONB_DISSLW = Port.PORTB, *RegisterBit.IOCON_DISSLW
    IOCONA_SEQOP = Port.PORTA, *RegisterBit.IOCON_SEQOP
    IOCONB_SEQOP = Port.PORTB, *RegisterBit.IOCON_SEQOP
    IOCONA_MIRROR = Port.PORTA, *RegisterBit.IOCON_MIRROR
    IOCONB_MIRROR = Port.PORTB, *RegisterBit.IOCON_MIRROR
    IOCONA_BANK = Port.PORTA, *RegisterBit.IOCON_BANK
    IOCONB_BANK = Port.PORTB, *RegisterBit.IOCON_BANK

    GPPUA_PU0 = Port.PORTA, *RegisterBit.GPPU_PU0
    GPPUB_PU0 = Port.PORTB, *RegisterBit.GPPU_PU0
    GPPUA_PU1 = Port.PORTA, *RegisterBit.GPPU_PU1
    GPPUB_PU1 = Port.PORTB, *RegisterBit.GPPU_PU1
    GPPUA_PU2 = Port.PORTA, *RegisterBit.GPPU_PU2
    GPPUB_PU2 = Port.PORTB, *RegisterBit.GPPU_PU2
    GPPUA_PU3 = Port.PORTA, *RegisterBit.GPPU_PU3
    GPPUB_PU3 = Port.PORTB, *RegisterBit.GPPU_PU3
    GPPUA_PU4 = Port.PORTA, *RegisterBit.GPPU_PU4
    GPPUB_PU4 = Port.PORTB, *RegisterBit.GPPU_PU4
    GPPUA_PU5 = Port.PORTA, *RegisterBit.GPPU_PU5
    GPPUB_PU5 = Port.PORTB, *RegisterBit.GPPU_PU5
    GPPUA_PU6 = Port.PORTA, *RegisterBit.GPPU_PU6
    GPPUB_PU6 = Port.PORTB, *RegisterBit.GPPU_PU6
    GPPUA_PU7 = Port.PORTA, *RegisterBit.GPPU_PU7
    GPPUB_PU7 = Port.PORTB, *RegisterBit.GPPU_PU7

    INTFA_INT0 = Port.PORTA, *RegisterBit.INTF_INT0
    INTFB_INT0 = Port.PORTB, *RegisterBit.INTF_INT0
    INTFA_INT1 = Port.PORTA, *RegisterBit.INTF_INT1
    INTFB_INT1 = Port.PORTB, *RegisterBit.INTF_INT1
    INTFA_INT2 = Port.PORTA, *RegisterBit.INTF_INT2
    INTFB_INT2 = Port.PORTB, *RegisterBit.INTF_INT2
    INTFA_INT3 = Port.PORTA, *RegisterBit.INTF_INT3
    INTFB_INT3 = Port.PORTB, *RegisterBit.INTF_INT3
    INTFA_INT4 = Port.PORTA, *RegisterBit.INTF_INT4
    INTFB_INT4 = Port.PORTB, *RegisterBit.INTF_INT4
    INTFA_INT5 = Port.PORTA, *RegisterBit.INTF_INT5
    INTFB_INT5 = Port.PORTB, *RegisterBit.INTF_INT5
    INTFA_INT6 = Port.PORTA, *RegisterBit.INTF_INT6
    INTFB_INT6 = Port.PORTB, *RegisterBit.INTF_INT6
    INTFA_INT7 = Port.PORTA, *RegisterBit.INTF_INT7
    INTFB_INT7 = Port.PORTB, *RegisterBit.INTF_INT7

    INTCAPA_ICP0 = Port.PORTA, *RegisterBit.INTCAP_ICP0
    INTCAPB_ICP0 = Port.PORTB, *RegisterBit.INTCAP_ICP0
    INTCAPA_ICP1 = Port.PORTA, *RegisterBit.INTCAP_ICP1
    INTCAPB_ICP1 = Port.PORTB, *RegisterBit.INTCAP_ICP1
    INTCAPA_ICP2 = Port.PORTA, *RegisterBit.INTCAP_ICP2
    INTCAPB_ICP2 = Port.PORTB, *RegisterBit.INTCAP_ICP2
    INTCAPA_ICP3 = Port.PORTA, *RegisterBit.INTCAP_ICP3
    INTCAPB_ICP3 = Port.PORTB, *RegisterBit.INTCAP_ICP3
    INTCAPA_ICP4 = Port.PORTA, *RegisterBit.INTCAP_ICP4
    INTCAPB_ICP4 = Port.PORTB, *RegisterBit.INTCAP_ICP4
    INTCAPA_ICP5 = Port.PORTA, *RegisterBit.INTCAP_ICP5
    INTCAPB_ICP5 = Port.PORTB, *RegisterBit.INTCAP_ICP5
    INTCAPA_ICP6 = Port.PORTA, *RegisterBit.INTCAP_ICP6
    INTCAPB_ICP6 = Port.PORTB, *RegisterBit.INTCAP_ICP6
    INTCAPA_ICP7 = Port.PORTA, *RegisterBit.INTCAP_ICP7
    INTCAPB_ICP7 = Port.PORTB, *RegisterBit.INTCAP_ICP7

    GPIOA_GP0 = Port.PORTA, *RegisterBit.GPIO_GP0
    GPIOB_GP0 = Port.PORTB, *RegisterBit.GPIO_GP0
    GPIOA_GP1 = Port.PORTA, *RegisterBit.GPIO_GP1
    GPIOB_GP1 = Port.PORTB, *RegisterBit.GPIO_GP1
    GPIOA_GP2 = Port.PORTA, *RegisterBit.GPIO_GP2
    GPIOB_GP2 = Port.PORTB, *RegisterBit.GPIO_GP2
    GPIOA_GP3 = Port.PORTA, *RegisterBit.GPIO_GP3
    GPIOB_GP3 = Port.PORTB, *RegisterBit.GPIO_GP3
    GPIOA_GP4 = Port.PORTA, *RegisterBit.GPIO_GP4
    GPIOB_GP4 = Port.PORTB, *RegisterBit.GPIO_GP4
    GPIOA_GP5 = Port.PORTA, *RegisterBit.GPIO_GP5
    GPIOB_GP5 = Port.PORTB, *RegisterBit.GPIO_GP5
    GPIOA_GP6 = Port.PORTA, *RegisterBit.GPIO_GP6
    GPIOB_GP6 = Port.PORTB, *RegisterBit.GPIO_GP6
    GPIOA_GP7 = Port.PORTA, *RegisterBit.GPIO_GP7
    GPIOB_GP7 = Port.PORTB, *RegisterBit.GPIO_GP7

    OLATA_OL0 = Port.PORTA, *RegisterBit.OLAT_OL0
    OLATB_OL0 = Port.PORTB, *RegisterBit.OLAT_OL0
    OLATA_OL1 = Port.PORTA, *RegisterBit.OLAT_OL1
    OLATB_OL1 = Port.PORTB, *RegisterBit.OLAT_OL1
    OLATA_OL2 = Port.PORTA, *RegisterBit.OLAT_OL2
    OLATB_OL2 = Port.PORTB, *RegisterBit.OLAT_OL2
    OLATA_OL3 = Port.PORTA, *RegisterBit.OLAT_OL3
    OLATB_OL3 = Port.PORTB, *RegisterBit.OLAT_OL3
    OLATA_OL4 = Port.PORTA, *RegisterBit.OLAT_OL4
    OLATB_OL4 = Port.PORTB, *RegisterBit.OLAT_OL4
    OLATA_OL5 = Port.PORTA, *RegisterBit.OLAT_OL5
    OLATB_OL5 = Port.PORTB, *RegisterBit.OLAT_OL5
    OLATA_OL6 = Port.PORTA, *RegisterBit.OLAT_OL6
    OLATB_OL6 = Port.PORTB, *RegisterBit.OLAT_OL6
    OLATA_OL7 = Port.PORTA, *RegisterBit.OLAT_OL7
    OLATB_OL7 = Port.PORTB, *RegisterBit.OLAT_OL7


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
    _data_byte_count: int

    @property
    def data_bytes(self) -> list[int]:
        return [(1 << MCP23S17.SPI_WORD_BIT_COUNT) - 1] * self.data_byte_count

    @property
    def data_byte_count(self) -> int:
        return self._data_byte_count


@dataclass
class Write(Operation):
    READ_OR_WRITE_BIT: ClassVar[int] = 0
    _data_bytes: list[int]

    @property
    def data_bytes(self) -> list[int]:
        return self._data_bytes

    @property
    def data_byte_count(self) -> int:
        return len(self.data_bytes)


@dataclass
class MCP23S17:
    """A Python driver for Microchip Technology MCP23S17 16-Bit I/O
    Expander with Serial Interface
    """

    SPI_MODES: ClassVar[tuple[int, int]] = 0b00, 0b11
    """The supported spi modes."""
    MAX_SPI_MAX_SPEED: ClassVar[float] = 10e6
    """The supported maximum spi maximum speed."""
    SPI_BIT_ORDER: ClassVar[str] = 'msb'
    """The supported spi bit order."""
    SPI_WORD_BIT_COUNT: ClassVar[int] = 8
    """The supported spi number of bits per word."""
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
    _mode: Mode = field(default=Mode.SIXTEEN_BIT_MODE, init=False)

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
    def mode(self) -> Mode:
        return self._mode

    @mode.setter
    def mode(self, value: Mode) -> None:
        self.write_bit(
            *PortRegisterBit.IOCONA_BANK,  # type: ignore[call-arg]
            value == Mode.EIGHT_BIT_MODE,
        )

        self._mode = value

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

    def read(
            self,
            register_address: int,
            data_byte_count: int,
    ) -> list[int]:
        return self.operate(
            Read(self.hardware_address, register_address, data_byte_count),
        )

    def write(
            self,
            register_address: int,
            data_bytes: list[int],
    ) -> list[int]:
        return self.operate(
            Write(self.hardware_address, register_address, data_bytes),
        )

    def get_register_address(self, port: Port, register: Register) -> int:
        if self.mode == Mode.SIXTEEN_BIT_MODE:
            register_address = (register * 2) + (port == Port.PORTB)
        else:
            register_address = ((port == Port.PORTB) * 0x10) | register

        return register_address

    def read_register(
            self,
            port: Port,
            register: Register,
            data_byte_count: int = 1,
    ) -> list[int]:
        return self.read(
            self.get_register_address(port, register),
            data_byte_count,
        )

    def write_register(
            self,
            port: Port,
            register: Register,
            data_bytes: list[int],
    ) -> list[int]:
        return self.write(
            self.get_register_address(port, register),
            data_bytes,
        )

    def read_bit(
            self,
            port: Port,
            register: Register,
            bit: int,
    ) -> bool:
        (data_byte,) = self.read_register(port, register)

        return bool(data_byte & (1 << bit))

    def write_bit(
            self,
            port: Port,
            register: Register,
            bit: int,
            value: bool,
    ) -> None:
        (data_byte,) = self.read_register(port, register)

        if bool(data_byte & (1 << bit)) != value:
            data_byte ^= 1 << bit

            self.write_register(port, register, [data_byte])

    @dataclass
    class Line:
        mcp23s17: MCP23S17
        port: Port
        bit: int
        direction: str
        inverted: bool = False

        def __post_init__(self) -> None:
            match self.direction:
                case 'in':
                    value = True
                case 'out':
                    value = False
                case _:
                    raise ValueError(f'unknown direction {self.direction}')

            self.mcp23s17.write_bit(
                self.port,
                Register.GPIO,
                self.bit,
                value,
            )

        def read(self) -> bool:
            value = self.mcp23s17.read_bit(self.port, Register.GPIO, self.bit)

            if self.inverted:
                value = not value

            return value

        def write(self, value: bool) -> None:
            if self.inverted:
                value = not value

            self.mcp23s17.write_bit(self.port, Register.GPIO, self.bit, value)

    def get_line(
            self,
            port: Port,
            bit: int,
            direction: str,
            inverted: bool = False,
    ) -> Line:
        return self.Line(self, port, bit, direction, inverted)

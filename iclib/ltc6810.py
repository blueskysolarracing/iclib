from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from time import sleep as _sleep
from typing import ClassVar
from warnings import warn

from periphery import SPI

from iclib.utilities import lsb_bits_to_byte, msb_bits_to_byte


@dataclass
class LTC6810:
    SPI_MODE: ClassVar[int] = 0b11
    """The supported spi mode."""
    MIN_SPI_MAX_SPEED: ClassVar[float] = 3e6
    """The supported minimum spi maximum speed."""
    MAX_SPI_MAX_SPEED: ClassVar[float] = 3.5e6
    """The supported maximum spi maximum speed."""
    SPI_BIT_ORDER: ClassVar[str] = 'msb'
    """The supported spi bit order."""
    SPI_WORD_BIT_COUNT: ClassVar[int] = 8
    """The supported spi number of bits per word."""
    spi: SPI
    """The SPI for the ADC device."""

    def __post_init__(self) -> None:
        if self.spi.mode != self.SPI_MODE:
            raise ValueError('unsupported spi mode')
        elif not (
                self.MIN_SPI_MAX_SPEED
                <= self.spi.max_speed
                <= self.MAX_SPI_MAX_SPEED
        ):
            raise ValueError('unsupported spi maximum speed')
        elif self.spi.bit_order != self.SPI_BIT_ORDER:
            raise ValueError('unsupported spi bit order')
        elif self.spi.bits_per_word != self.SPI_WORD_BIT_COUNT:
            raise ValueError('unsupported spi number of bits per word')

        if self.spi.extra_flags:
            warn(f'unknown spi extra flags {self.spi.extra_flags}')

    @classmethod
    def get_voltage(cls, data_bytes: list[int]) -> float:
        """Parse the voltage from data bytes.

        The data bytes is expected to be of length ``2``.

        On Page 24, the datasheet states that each LSB is equivalent to
        100µV. The full range of 16 bytes is from -0.8192V to +5.73V,
        but negative values are rounded to zero.

        :param data_bytes: The voltage data bytes (of length ``2``).
        :return: The voltage value.
        """
        assert len(data_bytes) == 2

        data = data_bytes[1] << 8 | data_bytes[0]

        return data / 10000

    @classmethod
    def get_packet_error_code_bytes(
            cls,
            data_bytes: Iterable[int],
    ) -> tuple[int, int]:
        """Generate packet error code (PEC) from data.

        Refer to Page 55 of LTC6810 datasheet.

        :return: The packet error code bytes.
        """
        PEC = [False] * 15
        PEC[4] = True

        for data_byte in data_bytes:
            for i in range(7, -1, -1):
                DIN = bool(data_byte & (1 << i))

                IN0 = DIN ^ PEC[14]
                IN3 = IN0 ^ PEC[2]
                IN4 = IN0 ^ PEC[3]
                IN7 = IN0 ^ PEC[6]
                IN8 = IN0 ^ PEC[7]
                IN10 = IN0 ^ PEC[9]
                IN14 = IN0 ^ PEC[13]

                PEC[14] = IN14
                PEC[13] = PEC[12]
                PEC[12] = PEC[11]
                PEC[11] = PEC[10]
                PEC[10] = IN10
                PEC[9] = PEC[8]
                PEC[8] = IN8
                PEC[7] = IN7
                PEC[6] = PEC[5]
                PEC[5] = PEC[4]
                PEC[4] = IN4
                PEC[3] = IN3
                PEC[2] = PEC[1]
                PEC[1] = PEC[0]
                PEC[0] = IN0

        PEC0 = lsb_bits_to_byte(*PEC[7:])
        PEC1 = lsb_bits_to_byte(*PEC[:7]) << 1

        return PEC0, PEC1

    @classmethod
    def get_address_poll_command_bytes(
            cls,
            address: int,
            command: int,
            poll_data_byte_count: int,
    ) -> list[int]:
        """Get address poll command bytes.

        Refer to Page 60 in the Datasheet.

        :param address: The device address.
        :param command: The command.
        :param poll_data_byte_count: The number of data bytes to be
                                     polled.
        :return: The address poll command bytes.
        """
        command_bytes = cls.get_address_command_bytes(address, command)
        poll_data_bytes = ((1 << 8) - 1,) * poll_data_byte_count

        return list(
            chain(
                command_bytes,
                cls.get_packet_error_code_bytes(command_bytes),
                poll_data_bytes,
            ),
        )

    @classmethod
    def get_address_write_command_bytes(
            cls,
            address: int,
            command: int,
            data_bytes: Iterable[int],
    ) -> list[int]:
        """Get address write command bytes.

        Refer to Page 60 in the Datasheet.

        :param address: The device address.
        :param command: The command.
        :param data_bytes: The data bytes to be written.
        :return: The address read command bytes.
        """
        command_bytes = cls.get_address_command_bytes(address, command)
        data_bytes = tuple(data_bytes)

        return list(
            chain(
                command_bytes,
                cls.get_packet_error_code_bytes(command_bytes),
                data_bytes,
                cls.get_packet_error_code_bytes(data_bytes),
            ),
        )

    @classmethod
    def get_address_read_command_bytes(
            cls,
            address: int,
            command: int,
            data_byte_count: int,
    ) -> list[int]:
        """Get address read command bytes.

        Refer to Page 60 in the Datasheet.

        :param address: The device address.
        :param command: The command.
        :param data_byte_count: The number of data bytes to be read.
        :return: The address read command bytes.
        """
        data_bytes = ((1 << 8) - 1,) * data_byte_count

        return cls.get_address_write_command_bytes(
            address,
            command,
            data_bytes,
        )

    @classmethod
    def get_broadcast_command_bytes(cls, command: int) -> tuple[int, int]:
        """Get broadcast command bytes.

        Refer to Page 60 in the Datasheet.

        :param command: The command.
        :return: The broadcast command bytes.
        """
        CMD0 = command >> 8
        CMD1 = command & ((1 << 8) - 1)

        return CMD0, CMD1

    @classmethod
    def get_address_command_bytes(
            cls,
            address: int,
            command: int,
    ) -> tuple[int, int]:
        """Get address command bytes.

        Refer to Page 60 in the Datasheet.

        :param address: The device address.
        :param command: The command.
        :return: The address command bytes.
        """
        CMD0, CMD1 = cls.get_broadcast_command_bytes(command)
        CMD0 |= (1 << 7) | (address << 3)

        return CMD0, CMD1

    def wakeup(self, sleep: bool = True) -> None:
        """Wake up the serial interface (Page 54).

        :param sleep: Sleep for a required period of time after wakeup.
        :return: ``None``.
        """
        self.spi.transfer([0])

        if sleep:
            _sleep(10e-6)

    class CHMode(Enum):
        """The CH ADC Modes, as defined in Page 63 of datasheet."""

        M27000 = 0b01, 524e-6, 200e-6
        """27 kHz Mode (Fast)."""
        M14000 = 0b01, 699e-6, 229e-6
        """14 kHz Mode."""
        M7000 = 0b10, 1.2e-3, 404e-6
        """7 kHz Mode (Normal)."""
        M3000 = 0b10, 1.9e-3, 520e-6
        """3 kHz Mode."""
        M2000 = 0b11, 3.3e-3, 753e-6
        """2 kHz Mode."""
        M1000 = 0b00, 6.1e-3, 1.2e-3
        """1 kHz Mode."""
        M422 = 0b00, 12e-3, 2.1e-3
        """422Hz Mode."""
        M26 = 0b11, 201e-3, 34e-3
        """26 Hz Mode (Filtered)."""

        def __init__(
                self,
                mode: int,
                all_cells_total_conversion_time: float,
                cell_total_conversion_time: float,
        ):
            self.mode: int = mode
            self.all_cells_total_conversion_time: float = (
                all_cells_total_conversion_time
            )
            self.cell_total_conversion_time: float = (
                cell_total_conversion_time
            )

    def ADCV(
            self,
            ch_mode: CHMode,
            DCP: bool,
            CH: int,
            address: int | None = None,
            sleep: bool = True,
    ) -> None:
        """Start cell voltage ADC conversion and poll status. Refer to
        Table 40 (Page 61) of datasheet.

        DCP values:

        - ``False``: discharge not permitted.
        - ``True``: discharge permitted.

        CH values:

        - ``0b000``: all cells.
        - ``0b001``: Cell 1.
        - ``0b010``: Cell 2.
        - ``0b011``: Cell 3.
        - ``0b100``: Cell 4.
        - ``0b101``: Cell 5.
        - ``0b110``: Cell 6.

        :param ch_mode: The ADC mode.
        :param DCP: Discharge permitted.
        :param CH: GPIO selection for ADC conversion.
        :param address: The optional address.
        :param sleep: Sleep for required period of time.
        :return: ``None``.
        """
        command = 0b01001100000
        command |= ch_mode.mode << 7
        command |= DCP << 4
        command |= CH

        if address is None:
            raise NotImplementedError
        else:
            transmitted_bytes = self.get_address_poll_command_bytes(
                address,
                command,
                0,
            )

        self.spi.transfer(transmitted_bytes)

        if sleep:
            if CH:
                timeout = ch_mode.cell_total_conversion_time
            else:
                timeout = ch_mode.all_cells_total_conversion_time

            _sleep(timeout)

    @dataclass
    class CVAR:
        """Cell voltage register group A."""

        C1V: float
        C2V: float
        C3V: float

    def RDCVA(self, address: int | None = None) -> CVAR:
        """Read cell voltage register group A. Refer to Table 40 (Page
        61) on datasheet.

        :param address: The optional address.
        :return: ``None``.
        """
        if address is None:
            raise NotImplementedError
        else:
            transmitted_bytes = self.get_address_read_command_bytes(
                address,
                0b00000000100,
                6,
            )

        received_bytes = self.spi.transfer(transmitted_bytes)[-6:]

        assert isinstance(received_bytes, list)

        return self.CVAR(
            self.get_voltage(received_bytes[0:2]),
            self.get_voltage(received_bytes[2:4]),
            self.get_voltage(received_bytes[4:6]),
        )

    @dataclass
    class CVBR:
        """Cell voltage register group B."""

        C4V: float
        C5V: float
        C6V: float

    def RDCVB(self, address: int | None = None) -> CVBR:
        """Read cell voltage register group B. Refer to Table 40 (Page
        61) on datasheet.

        :param address: The optional address.
        :return: ``None``.
        """
        if address is None:
            raise NotImplementedError
        else:
            transmitted_bytes = self.get_address_read_command_bytes(
                address,
                0b00000000110,
                6,
            )

        received_bytes = self.spi.transfer(transmitted_bytes)[-6:]

        assert isinstance(received_bytes, list)

        return self.CVBR(
            self.get_voltage(received_bytes[0:2]),
            self.get_voltage(received_bytes[2:4]),
            self.get_voltage(received_bytes[4:6]),
        )

    class CHGMode(Enum):
        """The CHG ADC Modes, as defined in Page 63 of datasheet."""

        M27000 = 0b01, 521e-6, 200e-6
        """27 kHz Mode (Fast)."""
        M14000 = 0b01, 695e-6, 229e-6
        """14 kHz Mode."""
        M7000 = 0b10, 1.2e-3, 403e-6
        """7 kHz Mode (Normal)."""
        M3000 = 0b10, 1.9e-3, 520e-6
        """3 kHz Mode."""
        M2000 = 0b11, 3.3e-3, 752e-6
        """2 kHz Mode."""
        M1000 = 0b00, 6e-3, 1.2e-3
        """1 kHz Mode."""
        M422 = 0b00, 12e-3, 2.1e-3
        """422Hz Mode."""
        M26 = 0b11, 183e-3, 34e-3
        """26 Hz Mode (Filtered)."""

        def __init__(
                self,
                mode: int,
                all_cells_total_conversion_time: float,
                cell_total_conversion_time: float,
        ):
            self.mode: int = mode
            self.all_cells_total_conversion_time: float = (
                all_cells_total_conversion_time
            )
            self.cell_total_conversion_time: float = (
                cell_total_conversion_time
            )

    def AXOW(
            self,
            chg_mode: CHGMode,
            PUP: bool,
            CHG: int,
            address: int | None = None,
            sleep: bool = True,
    ) -> None:
        """Start GPIOS/Cell 0/REF2 ADC open wire conversion. Refer to
        Table 40 (Page 62) on datasheet.

        PUP values:

        - ``False``: Pull-down current.
        - ``True``: Pull-up current.

        CHG values:

        - ``0b000``: S0, GPIO 1-4, 2nd reference.
        - ``0b001``: S0.
        - ``0b010``: GPIO 1.
        - ``0b011``: GPIO 2.
        - ``0b100``: GPIO 3.
        - ``0b101``: GPIO 4.
        - ``0b110``: 2nd reference.

        :param chg_mode: The ADC mode.
        :param PUP: Pull-up/pull-down current for open wire conversions.
        :param CHG: GPIO selection for ADC conversion.
        :param address: The optional address.
        :param sleep: Sleep for required period of time.
        :return: ``None``.
        """
        command = 0b10000010000
        command |= chg_mode.mode << 7
        command |= PUP << 6
        command |= CHG

        if address is None:
            raise NotImplementedError
        else:
            transmitted_bytes = self.get_address_poll_command_bytes(
                address,
                command,
                0,
            )

        self.spi.transfer(transmitted_bytes)

        if sleep:
            if CHG:
                timeout = chg_mode.cell_total_conversion_time
            else:
                timeout = chg_mode.all_cells_total_conversion_time

            _sleep(timeout)

    @dataclass
    class AVAR:
        S0V: float
        G1V: float
        G2V: float

    def RDAUXA(self, address: int | None = None) -> AVAR:
        """Read auxiliary register group A. Refer to Table 40 (Page 61)
        on datasheet.

        :param address: The optional address.
        :return: ``None``.
        """
        if address is None:
            raise NotImplementedError
        else:
            transmitted_bytes = self.get_address_read_command_bytes(
                address,
                0b00000001100,
                6,
            )

        received_bytes = self.spi.transfer(transmitted_bytes)[-6:]

        assert isinstance(received_bytes, list)

        return self.AVAR(
            self.get_voltage(received_bytes[0:2]),
            self.get_voltage(received_bytes[2:4]),
            self.get_voltage(received_bytes[4:6]),
        )

    @dataclass
    class AVBR:
        """Auxiliary register group B."""

        G3V: float
        G4V: float
        REF: float

    def RDAUXB(self, address: int | None = None) -> AVBR:
        """Read auxiliary register group B. Refer to Table 40 (Page 61)
        on datasheet.

        :param address: The optional address.
        :return: ``None``.
        """
        if address is None:
            raise NotImplementedError
        else:
            transmitted_bytes = self.get_address_read_command_bytes(
                address,
                0b00000001110,
                6,
            )

        received_bytes = self.spi.transfer(transmitted_bytes)[-6:]

        assert isinstance(received_bytes, list)

        return self.AVBR(
            self.get_voltage(received_bytes[0:2]),
            self.get_voltage(received_bytes[2:4]),
            self.get_voltage(received_bytes[4:6]),
        )

    @dataclass
    class CFGR(Iterable[int]):
        """The configuration register group (Table 42)."""

        GPIO4: bool = False
        GPIO3: bool = False
        GPIO2: bool = False
        GPIO1: bool = False
        REFON: bool = False
        DTEN: bool = False
        ADCOPT: bool = False
        VUV: int = 0
        VOV: int = 0
        DCC0: bool = False
        MCAL: bool = False
        DCC6: bool = False
        DCC5: bool = False
        DCC4: bool = False
        DCC3: bool = False
        DCC2: bool = False
        DCC1: bool = False
        DCTO: int = 0
        SCONV: bool = False
        FDRF: bool = False
        DIS_RED: bool = False
        DTMEN: bool = False

        def __iter__(self) -> Iterator[int]:
            return iter(self.bytes)

        @property
        def bytes(self) -> tuple[int, ...]:
            CFGR0 = msb_bits_to_byte(
                False,
                self.GPIO4,
                self.GPIO3,
                self.GPIO2,
                self.GPIO1,
                self.REFON,
                self.DTEN,
                self.ADCOPT,
            )
            CFGR1 = self.VUV & ((1 << 8) - 1)
            CFGR2 = ((self.VOV & ((1 << 4) - 1)) << 4) | (self.VUV >> 8)
            CFGR3 = self.VOV >> 4
            CFGR4 = msb_bits_to_byte(
                self.DCC0,
                self.MCAL,
                self.DCC6,
                self.DCC5,
                self.DCC4,
                self.DCC3,
                self.DCC2,
                self.DCC1,
            )
            CFGR5 = (
                (self.DCTO << 4)
                | msb_bits_to_byte(
                    False,
                    False,
                    False,
                    False,
                    self.SCONV,
                    self.FDRF,
                    self.DIS_RED,
                    self.DTMEN,
                )
            )

            return CFGR0, CFGR1, CFGR2, CFGR3, CFGR4, CFGR5

    def WRCFG(self, CFGR: CFGR, address: int | None = None) -> None:
        """Write configuration register group. Refer to Table 40 (Page
        61) on datasheet.

        :param CFGR: The configuration register group.
        :param address: The optional address.
        :return: ``None``.
        """
        if address is None:
            raise NotImplementedError
        else:
            transmitted_bytes = self.get_address_write_command_bytes(
                address,
                0b00000000001,
                CFGR,
            )

        self.spi.transfer(transmitted_bytes)

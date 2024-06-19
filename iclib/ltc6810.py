from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from time import sleep as _sleep
from typing import ClassVar
from warnings import warn

from periphery import SPI


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

        PEC0 = 0
        PEC1 = 0

        for i, PEC_bit in enumerate(PEC):
            bit = PEC_bit << i

            if i < 7:
                PEC1 |= bit << 1
            else:
                PEC0 |= bit >> 7

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
        :param poll_data_byte_count: The number of data bytes to be polled.
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
        command_bytes = cls.get_broadcast_command_bytes(command)
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

    class ADCMode(Enum):
        """The ADC Modes, as defined in Page 63 of datasheet."""

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

    def start_cell_voltage_adc_conversion_and_poll_status(
            self,
            adc_mode: ADCMode,
            channel: int,
            address: int | None = None,
            sleep: bool = True,
    ) -> None:
        command = 0b01001100000
        command |= adc_mode.mode << 7
        command |= channel

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
            if channel:
                timeout = adc_mode.cell_total_conversion_time
            else:
                timeout = adc_mode.all_cells_total_conversion_time

            _sleep(timeout)

    @dataclass
    class CellVoltageRegisterGroupA:
        C1V: float
        C2V: float
        C3V: float

    def read_cell_voltage_register_group_a(
            self,
            address: int | None = None,
    ) -> CellVoltageRegisterGroupA:
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

        return self.CellVoltageRegisterGroupA(
            self.get_voltage(received_bytes[0:2]),
            self.get_voltage(received_bytes[2:4]),
            self.get_voltage(received_bytes[4:6]),
        )

    @dataclass
    class CellVoltageRegisterGroupB:
        C4V: float
        C5V: float
        C6V: float

    def read_cell_voltage_register_group_b(
            self,
            address: int | None = None,
    ) -> CellVoltageRegisterGroupB:
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

        return self.CellVoltageRegisterGroupB(
            self.get_voltage(received_bytes[0:2]),
            self.get_voltage(received_bytes[2:4]),
            self.get_voltage(received_bytes[4:6]),
        )

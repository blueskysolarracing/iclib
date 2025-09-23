"""This module implements the TMAG5273 driver."""

from dataclasses import dataclass, field
from enum import Enum, IntEnum

from periphery import I2C

from iclib.utilities import twos_complement


class Register(IntEnum):
    DEVICE_CONFIG_1 = 0x00
    DEVICE_CONFIG_2 = 0x01
    SENSOR_CONFIG_1 = 0x02
    SENSOR_CONFIG_2 = 0x03
    X_THR_CONFIG = 0x04
    Y_THR_CONFIG = 0x05
    Z_THR_CONFIG = 0x06
    T_CONFIG = 0x07
    INT_CONFIG_1 = 0x08
    MAG_GAIN_CONFIG = 0x09
    MAG_OFFSET_CONFIG_1 = 0x0A
    MAG_OFFSET_CONFIG_2 = 0x0B
    I2C_ADDRESS = 0x0C
    DEVICE_ID = 0x0D
    MANUFACTURER_ID_LSB = 0x0E
    MANUFACTURER_ID_MSB = 0x0F
    T_MSB_RESULT = 0x10
    T_LSB_RESULT = 0x11
    X_MSB_RESULT = 0x12
    X_LSB_RESULT = 0x13
    Y_MSB_RESULT = 0x14
    Y_LSB_RESULT = 0x15
    Z_MSB_RESULT = 0x16
    Z_LSB_RESULT = 0x17
    CONV_STATUS = 0x18
    ANGLE_RESULT_MSB = 0x19
    ANGLE_RESULT_LSB = 0x1A
    MAGNITUDE_RESULT = 0x1B
    DEVICE_STATUS = 0x1C


class Variant(Enum):
    A1 = 0x01, 0x35, 0.04
    B1 = 0x02, 0x22, 0.04
    C1 = 0x03, 0x78, 0.04
    D1 = 0x04, 0x44, 0.04
    A2 = 0x05, 0x35, 0.133
    B2 = 0x06, 0x22, 0.133
    C2 = 0x07, 0x78, 0.133
    D2 = 0x08, 0x44, 0.133

    def __init__(self, variant: int, address: int, bound: float) -> None:
        self.variant = variant
        self.address = address
        self.bound = bound


class Enable(IntEnum):
    DISABLE = 0x00
    ENABLE = 0x01


class MagnetTemperatureCoeff(IntEnum):
    DISABLE = 0x00
    NdBFe = 0x01
    CERAMIC = 0x03


class ConversionAvg(IntEnum):
    SAMPLE_1X = 0x00
    SAMPLE_2X = 0x01
    SAMPLE_4X = 0x02
    SAMPLE_8X = 0x03
    SAMPLE_16X = 0x04
    SAMPLE_32X = 0x05


class I2CReadMode(IntEnum):
    STANDARD_3BYTE = 0x00
    SHORT_16BIT_DATA = 0x01
    SHORT_8BIT_DATA = 0x02


class OperatingMode(IntEnum):
    STANDBY = 0x00
    SLEEP = 0x01
    CONTINUOUS = 0x02
    WAKE_UP_AND_SLEEP = 0x03


class MagneticChannel(Enum):
    DISABLE = 0x00, 0
    X = 0x01, 1
    Y = 0x02, 1
    XY = 0x03, 2
    Z = 0x04, 1
    ZX = 0x05, 2
    YZ = 0x06, 2
    XYZ = 0x07, 3
    XYX = 0x08, 3
    YXY = 0x09, 3
    YZY = 0x0A, 3
    XZX = 0x0B, 3

    def __init__(self, code: int, size: int) -> None:
        self.code = code
        self.size = size


class MagneticRange(IntEnum):
    DEFAULT = 0x00
    EXTENDED = 0x01


@dataclass
class TMAH5273:
    """A Python driver for Texas Instruments TMAG5273 Hall-Effect sensor"""

    i2c: I2C
    """The I2C bus."""
    variant: Variant
    """The device version."""
    address: int = field(init=False)
    """The address on I2C bus."""
    magnetic_range_bound: float = field(init=False)
    _crc_enable: Enable = field(init=False, default=Enable.DISABLE)
    _magnet_temperature_coeff: MagnetTemperatureCoeff = field(
        init=False,
        default=MagnetTemperatureCoeff.DISABLE
    )
    _conversion_avg: ConversionAvg = field(
        init=False,
        default=ConversionAvg.SAMPLE_1X
    )
    _i2c_read_mode: I2CReadMode = field(
        init=False,
        default=I2CReadMode.STANDARD_3BYTE
    )
    _operating_mode: OperatingMode = field(
        init=False,
        default=OperatingMode.STANDBY
    )
    _magnetic_channel: MagneticChannel = field(
        init=False,
        default=MagneticChannel.DISABLE
    )
    _magnetic_range: MagneticRange = field(
        init=False,
        default=MagneticRange.DEFAULT
    )
    _temperature_enable: Enable = field(init=False, default=Enable.DISABLE)

    def __post_init__(self) -> None:
        self.address = self.variant.address
        self.magnetic_range_bound = self.variant.bound

    def write(self, register: Register, data: int) -> None:
        message = I2C.Message([register, data])

        self.i2c.transfer(self.address, [message])

    def read(self, register: Register, length: int) -> list[int]:
        if self.i2c_read_mode != I2CReadMode.STANDARD_3BYTE:
            self.i2c_read_mode = I2CReadMode.STANDARD_3BYTE

        if self.crc_enable == Enable.ENABLE:
            length = 5
        write_message = I2C.Message([register])
        read_message = I2C.Message([0] * length, read=True)
        self.i2c.transfer(self.address, [write_message, read_message])

        if self.crc_enable == Enable.ENABLE:
            received = list(read_message.data)
            received[4] = self.check_crc_error(received[0:4], received[4])
            return received

        return list(read_message.data)

    def close(self) -> None:
        self.i2c.close()

    def check_crc_error(self, data: list[int], cyc_byte: int) -> int:
        """
        Validate data with CRC byte

        return 0 if matching
        return 1 if not matching (error)
        """
        return 0

    @property
    def channels(self) -> list[float]:
        if self.i2c_read_mode == I2CReadMode.STANDARD_3BYTE:
            return list()

        length = self.magnetic_channel.size
        if self.temperature_enable == Enable.ENABLE:
            length += 1
        if self.i2c_read_mode == I2CReadMode.SHORT_16BIT_DATA:
            length *= 2
        if self.crc_enable == Enable.ENABLE:
            length += 1
        length += 1

        read_message = I2C.Message([0] * length, read=True)
        self.i2c.transfer(self.address, [read_message])

        received = list(read_message.data)
        result = []

        if self.i2c_read_mode == I2CReadMode.SHORT_16BIT_DATA:
            data_size = 2
        else:
            data_size = 1

        start_index = 0
        if self.temperature_enable == Enable.ENABLE:
            start_index = data_size
            result.append(self.parse_temperature(received[0:data_size]))
        for x in range(self.magnetic_channel.size):
            current_index = start_index + data_size * x
            result.append(self.parse_magnetic_field(
                received[current_index:current_index + data_size]
            ))

        if self.crc_enable == Enable.ENABLE:
            result.append(self.check_crc_error(received[0:-1], received[-1]))

        return result

    def parse_magnetic_field(self, bytes: list[int]) -> float:
        if self.i2c_read_mode == I2CReadMode.STANDARD_3BYTE:
            return float()

        if self.i2c_read_mode == I2CReadMode.SHORT_16BIT_DATA:
            raw_value = twos_complement(bytes[0] << 8 & bytes[1], 16)
            return raw_value / (2 ** 16) * 2 * self.magnetic_range_bound
        else:
            raw_value = twos_complement(bytes[0], 8)
            return raw_value / (2 ** 8) * 2 * self.magnetic_range_bound

    def parse_temperature(self, bytes: list[int]) -> float:
        """
        TODO
        Input: raw bytes (either 1 byte: only MSB or 2 bytes: [MSB, LSB])
        return the temperature according to datasheet 6.5.2.2
        """
        return float()

    @property
    def angle(self) -> float:
        """
        Read the register and then compute the value according to the formula
        (datasheet 6.5.2.3)
        """
        return float()

    @property
    def magnitude(self) -> float:
        """
        Read the register and then compute the value according to the formula
        (datasheet 6.5.2.3)
        """
        return float()

    @property
    def crc_enable(self) -> Enable:
        return self._crc_enable

    @crc_enable.setter
    def crc_enable(self, value: Enable) -> None:
        self.device_config_1(
            value,
            self._magnet_temperature_coeff,
            self._conversion_avg,
            self._i2c_read_mode,
        )

    @property
    def magnet_temperature_coeff(self) -> MagnetTemperatureCoeff:
        return self._magnet_temperature_coeff

    @magnet_temperature_coeff.setter
    def magnet_temperature_coeff(self, value: MagnetTemperatureCoeff) -> None:
        self.device_config_1(
            self._crc_enable,
            value,
            self._conversion_avg,
            self._i2c_read_mode,
        )

    @property
    def conversion_avg(self) -> ConversionAvg:
        return self._conversion_avg

    @conversion_avg.setter
    def conversion_avg(self, value: ConversionAvg) -> None:
        self.device_config_1(
            self._crc_enable,
            self._magnet_temperature_coeff,
            value,
            self._i2c_read_mode,
        )

    @property
    def i2c_read_mode(self) -> I2CReadMode:
        return self._i2c_read_mode

    @i2c_read_mode.setter
    def i2c_read_mode(self, value: I2CReadMode) -> None:
        self.device_config_1(
            self._crc_enable,
            self._magnet_temperature_coeff,
            self._conversion_avg,
            value,
        )

    def device_config_1(
            self,
            crc_enable: Enable,
            magnet_temperature_coeff: MagnetTemperatureCoeff,
            conversion_avg: ConversionAvg,
            i2c_read_mode: I2CReadMode,
    ) -> None:
        """Set parameters in DEVICE_CONFIG_1 register."""

        self._crc_enable = crc_enable
        self._angular_velocity_unit = magnet_temperature_coeff
        self._angle_unit = conversion_avg
        self._temperature_unit = i2c_read_mode
        raw_byte = (
            crc_enable << 7
            | magnet_temperature_coeff << 5
            | conversion_avg << 2
            | i2c_read_mode
        )

        self.write(Register.DEVICE_CONFIG_1, raw_byte)

    @property
    def operating_mode(self) -> OperatingMode:
        return self._operating_mode

    @operating_mode.setter
    def operating_mode(self, value: OperatingMode) -> None:
        original_byte = self.read(Register.DEVICE_CONFIG_2, 1)[0] & 0xFC
        send_byte = original_byte | value
        self.write(Register.DEVICE_CONFIG_2, send_byte)

    @property
    def magnetic_channel(self) -> MagneticChannel:
        return self._magnetic_channel

    @magnetic_channel.setter
    def magnetic_channel(self, value: MagneticChannel) -> None:
        original_byte = self.read(Register.SENSOR_CONFIG_1, 1)[0] & 0x0F
        send_byte = original_byte | value.code << 4
        self.write(Register.SENSOR_CONFIG_1, send_byte)

    @property
    def magnetic_range(self) -> MagneticRange:
        return self._magnetic_range

    @magnetic_range.setter
    def magnetic_range(self, value: MagneticRange) -> None:
        if value == MagneticRange.DEFAULT:
            self.magnetic_range_bound = self.variant.bound
        else:
            self.magnetic_range_bound = self.variant.bound * 2
        original_byte = self.read(Register.SENSOR_CONFIG_2, 1)[0] & 0xFC
        send_byte = original_byte | value << 1 | value
        self.write(Register.SENSOR_CONFIG_2, send_byte)

    @property
    def temperature_enable(self) -> Enable:
        return self._temperature_enable

    @temperature_enable.setter
    def temperature_enable(self, value: Enable) -> None:
        original_byte = self.read(Register.T_CONFIG, 1)[0] & 0xFE
        send_byte = original_byte | value
        self.write(Register.T_CONFIG, send_byte)

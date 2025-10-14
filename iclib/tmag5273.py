"""This module implements the TMAG5273 driver."""

from dataclasses import dataclass, field
from enum import Enum, IntEnum

from periphery import I2C

from iclib.utilities import twos_complement, bit_getter


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


class AngleEnable(IntEnum):
    DISABLE = 0x00
    XY = 0x01
    YZ = 0x02
    XZ = 0x03


class MagneticRange(IntEnum):
    DEFAULT = 0x00
    EXTENDED = 0x01


@dataclass
class TMAG5273:
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
    _angle_enable: AngleEnable = field(init=False, default=AngleEnable.DISABLE)
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
        previous_i2c_read_mode = self.i2c_read_mode
        revert_i2c_read_mode = False
        if previous_i2c_read_mode != I2CReadMode.STANDARD_3BYTE:
            self.i2c_read_mode = I2CReadMode.STANDARD_3BYTE
            revert_i2c_read_mode = True

        if self.crc_enable == Enable.ENABLE:
            length = 5
        write_message = I2C.Message([register])
        read_message = I2C.Message([0] * length, read=True)
        self.i2c.transfer(self.address, [write_message, read_message])

        if self.crc_enable == Enable.ENABLE:
            received = list(read_message.data)
            received[4] = self.check_crc_error(received[0:4], received[4])
            return received

        if revert_i2c_read_mode:
            self.i2c_read_mode = previous_i2c_read_mode

        return list(read_message.data)

    def close(self) -> None:
        self.i2c.close()

    def check_crc_error(self, data: list[int], cyc_byte: int) -> bool:
        """
        Validate data with CRC byte

        return True if matching
        return False if not matching (error)
        """
        c = 0xFF
        crc = [0] * 8

        b0 = bit_getter(0)
        b1 = bit_getter(1)
        b2 = bit_getter(2)
        b3 = bit_getter(3)
        b4 = bit_getter(4)
        b5 = bit_getter(5)
        b6 = bit_getter(6)
        b7 = bit_getter(7)

        for x in range(len(data)):
            d = data[x]
            crc[0] = b7(d) ^ b6(d) ^ b0(d) ^ b0(c) ^ b6(c) ^ b7(c)
            crc[1] = b6(d) ^ b1(d) ^ b0(d) ^ b0(c) ^ b1(c) ^ b6(c)
            crc[2] = (
                b6(d) ^ b2(d) ^ b1(d) ^ b0(d) ^ b0(c) ^ b1(c) ^ b2(c) ^ b6(c)
            )
            crc[3] = (
                b7(d) ^ b3(d) ^ b2(d) ^ b1(d) ^ b1(c) ^ b2(c) ^ b3(c) ^ b7(c)
            )
            crc[4] = b4(d) ^ b3(d) ^ b2(d) ^ b2(c) ^ b3(c) ^ b4(c)
            crc[5] = b5(d) ^ b4(d) ^ b3(d) ^ b3(c) ^ b4(c) ^ b5(c)
            crc[6] = b6(d) ^ b5(d) ^ b4(d) ^ b4(c) ^ b5(c) ^ b6(c)
            crc[7] = b7(d) ^ b6(d) ^ b5(d) ^ b5(c) ^ b6(c) ^ b7(c)

            c = 0x00
            for i in range(8):
                c |= (crc[i] & 0x1) << i

        return c == cyc_byte

    @property
    def channels(self) -> tuple[list[float], bool | None]:
        if self.i2c_read_mode == I2CReadMode.STANDARD_3BYTE:
            return ([], None)

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
        crc = None

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
            crc = self.check_crc_error(received[0:-1], received[-1])

        return (result, crc)

    def parse_magnetic_field(self, bytes: list[int]) -> float:
        if len(bytes) == 2:
            raw = twos_complement((bytes[0] << 8 | bytes[1]) & 0xFFFF, 16)
            return raw / (2 ** 16) * 2 * self.magnetic_range_bound
        if len(bytes) == 1:
            raw = twos_complement(bytes[0] & 0xFF, 8)
            return raw / (2 ** 8) * 2 * self.magnetic_range_bound
        return float()

    def parse_temperature(self, data: list[int]) -> float:
        TSENS_T0 = 25.0
        TADC_T0 = 17508
        TADC_RES = 60.1

        if len(data) == 2:
            code = twos_complement(((data[0] << 8) | data[1]) & 0xFFFF, 16)
            return TSENS_T0 + (code - TADC_T0) / TADC_RES
        if len(data) == 1:
            code8 = twos_complement(data[0] & 0xFF, 8)
            return TSENS_T0 + (256 * (code8 - TADC_T0 / 256)) / TADC_RES

        return float()

    @property
    def angle(self) -> float:
        msb = self.read(Register.ANGLE_RESULT_MSB, 1)[0]
        lsb = self.read(Register.ANGLE_RESULT_LSB, 1)[0]
        word = ((msb << 8) | lsb) & 0xFFFF
        int_part = (word >> 4) & 0x1FF
        frac_part = (word & 0xF) / 16.0
        return float(int_part) + frac_part

    @property
    def magnitude(self) -> float:
        code = self.read(Register.MAGNITUDE_RESULT, 1)[0] & 0xFF
        return code / 0xFF

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
        self._magnet_temperature_coeff = magnet_temperature_coeff
        self._conversion_avg = conversion_avg
        self._i2c_read_mode = i2c_read_mode
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
        self._operating_mode = value
        original_byte = self.read(Register.DEVICE_CONFIG_2, 1)[0] & 0xFC
        send_byte = original_byte | value
        self.write(Register.DEVICE_CONFIG_2, send_byte)

    @property
    def magnetic_channel(self) -> MagneticChannel:
        return self._magnetic_channel

    @magnetic_channel.setter
    def magnetic_channel(self, value: MagneticChannel) -> None:
        self._magnetic_channel = value
        original_byte = self.read(Register.SENSOR_CONFIG_1, 1)[0] & 0x0F
        send_byte = original_byte | value.code << 4
        self.write(Register.SENSOR_CONFIG_1, send_byte)

    @property
    def angle_enable(self) -> AngleEnable:
        return self._angle_enable

    @angle_enable.setter
    def angle_enable(self, value: AngleEnable) -> None:
        self._angle_enable = value
        original_byte = self.read(Register.SENSOR_CONFIG_2, 1)[0] & 0xF3
        send_byte = original_byte | value << 2
        self.write(Register.SENSOR_CONFIG_2, send_byte)

    @property
    def magnetic_range(self) -> MagneticRange:
        return self._magnetic_range

    @magnetic_range.setter
    def magnetic_range(self, value: MagneticRange) -> None:
        if value == MagneticRange.DEFAULT:
            self.magnetic_range_bound = self.variant.bound
        else:
            self.magnetic_range_bound = self.variant.bound * 2
        self._magnetic_range = value
        original_byte = self.read(Register.SENSOR_CONFIG_2, 1)[0] & 0xFC
        send_byte = original_byte | value << 1 | value
        self.write(Register.SENSOR_CONFIG_2, send_byte)

    @property
    def temperature_enable(self) -> Enable:
        return self._temperature_enable

    @temperature_enable.setter
    def temperature_enable(self, value: Enable) -> None:
        self._temperature_enable = value
        original_byte = self.read(Register.T_CONFIG, 1)[0] & 0xFE
        send_byte = original_byte | value
        self.write(Register.T_CONFIG, send_byte)

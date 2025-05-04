"""This module implements the BNO055 driver."""

from dataclasses import dataclass, field
from enum import IntEnum
from logging import getLogger
from time import sleep
from typing import ClassVar

from periphery import I2C, GPIO

_logger = getLogger(__name__)


class Register(IntEnum):
    CHIP_ID = 0x00
    """Chip Identification Code."""
    ACC_ID = 0x01
    """Chip ID of accelerometer Device."""
    MAG_ID = 0x02
    """Chip ID of magnetometer Device."""
    GYR_ID = 0x03
    """Chip ID of gyroscope device."""
    SW_REV_ID_LSB = 0x04
    """Lower Byte of SW Revision ID."""
    SW_REV_ID_MSB = 0x05
    """Upper Byte of SW Revision ID."""
    BL_REV_ID = 0x06
    """Identifies the version of the bootloader in the microcontroller."""
    PAGE_ID = 0x07
    """Number of currently selected page."""
    ACC_DATA_X_LSB = 0x08
    ACC_DATA_X_MSB = 0x09
    ACC_DATA_Y_LSB = 0x0A
    ACC_DATA_Y_MSB = 0x0B
    ACC_DATA_Z_LSB = 0x0C
    ACC_DATA_Z_MSB = 0x0D
    MAG_DATA_X_LSB = 0x0E
    MAG_DATA_X_MSB = 0x0F
    MAG_DATA_Y_LSB = 0x10
    MAG_DATA_Y_MSB = 0x11
    MAG_DATA_Z_LSB = 0x12
    MAG_DATA_Z_MSB = 0x13
    GYR_DATA_X_LSB = 0x14
    GYR_DATA_X_MSB = 0x15
    GYR_DATA_Y_LSB = 0x16
    GYR_DATA_Y_MSB = 0x17
    GYR_DATA_Z_LSB = 0x18
    GYR_DATA_Z_MSB = 0x19
    EUL_DATA_X_LSB = 0x1A
    EUL_DATA_X_MSB = 0x1B
    EUL_DATA_Y_LSB = 0x1C
    EUL_DATA_Y_MSB = 0x1D
    EUL_DATA_Z_LSB = 0x1E
    EUL_DATA_Z_MSB = 0x1F
    QUA_DATA_W_LSB = 0x20
    QUA_DATA_W_MSB = 0x21
    QUA_DATA_X_LSB = 0x22
    QUA_DATA_X_MSB = 0x23
    QUA_DATA_Y_LSB = 0x24
    QUA_DATA_Y_MSB = 0x25
    QUA_DATA_Z_LSB = 0x26
    QUA_DATA_Z_MSB = 0x27
    LIA_DATA_X_LSB = 0x28
    LIA_DATA_X_MSB = 0x29
    LIA_DATA_Y_LSB = 0x2A
    LIA_DATA_Y_MSB = 0x2B
    LIA_DATA_Z_LSB = 0x2C
    LIA_DATA_Z_MSB = 0x2D
    GRV_DATA_X_LSB = 0x2E
    GRV_DATA_X_MSB = 0x2F
    GRV_DATA_Y_LSB = 0x30
    GRV_DATA_Y_MSB = 0x31
    GRV_DATA_Z_LSB = 0x32
    GRV_DATA_Z_MSB = 0x33
    TEMP = 0x34
    CALIB_STAT = 0x35
    UNIT_SEL = 0x3B
    OPR_MODE = 0x3D
    PWR_MODE = 0x3E
    SYS_TRIG = 0x3F


class OperationMode(IntEnum):
    ACCONLY = 0x1
    MAGONLY = 0x2
    GYROONLY = 0x3
    ACCMAG = 0x4
    ACCGYRO = 0x5
    MAGGYRO = 0x6
    AMG = 0x7
    IMU = 0x8
    COMPASS = 0x9
    M4G = 0xA
    NDOF_FMC_OFF = 0xB
    NDOF = 0xC


class Unit(IntEnum):
    MS2 = 0x0
    MG = 0x1
    DPS = 0x0
    RPS = 0x2
    DEGREES = 0x0
    RADIANS = 0x4
    CELSIUS = 0x0
    FAHRENHEIT = 0x10


@dataclass
class BNO055:
    ADDRESS: ClassVar[int] = 0x29
    RESET_TIMEOUT: ClassVar[float] = 2.5
    IMU_RESET_GPIO_DIRECTION: ClassVar[str] = 'out'
    IMU_RESET_GPIO_INVERTED: ClassVar[bool] = True
    i2c: I2C
    imu_reset_gpio: GPIO
    _acceleration_unit: Unit = field(init=False, default=Unit.MS2)
    _angular_velocity_unit: Unit = field(init=False, default=Unit.DPS)
    _angle_unit: Unit = field(init=False, default=Unit.DEGREES)
    _temperature_unit: Unit = field(init=False, default=Unit.CELSIUS)

    @dataclass
    class Vector:
        x: float
        y: float
        z: float

    @dataclass
    class Quaternion:
        w: float
        x: float
        y: float
        z: float

    def __post_init__(self) -> None:
        if self.imu_reset_gpio.direction != self.IMU_RESET_GPIO_DIRECTION:
            raise ValueError('invalid GPIO direction')
        elif self.imu_reset_gpio.inverted != self.IMU_RESET_GPIO_INVERTED:
            raise ValueError('invalid GPIO inverted status')

    def select_operation_mode(
            self,
            accelerometer: bool,
            gyroscope: bool,
            magnetometer: bool,
    ) -> None:
        if (
                accelerometer is True
                and gyroscope is True
                and magnetometer is True
        ):
            self.write(Register.OPR_MODE, OperationMode.AMG)
        elif accelerometer is True and gyroscope is True:
            self.write(Register.OPR_MODE, OperationMode.ACCGYRO)
        elif accelerometer is True and magnetometer is True:
            self.write(Register.OPR_MODE, OperationMode.ACCMAG)
        elif magnetometer is True and gyroscope is True:
            self.write(Register.OPR_MODE, OperationMode.MAGGYRO)
        elif accelerometer is True:
            self.write(Register.OPR_MODE, OperationMode.ACCONLY)
        elif gyroscope is True:
            self.write(Register.OPR_MODE, OperationMode.GYROONLY)
        elif magnetometer is True:
            self.write(Register.OPR_MODE, OperationMode.MAGONLY)
        else:
            self.write(Register.OPR_MODE, 0)

        _logger.info('Operation mode set for BNO055')

    def write(self, register: Register, data: int) -> None:
        message = I2C.Message([register, data])

        self.i2c.transfer(self.ADDRESS, [message])

    def read(self, register: Register, length: int) -> list[int]:
        write_message = I2C.Message([register])
        read_message = I2C.Message([0] * length, read=True)

        self.i2c.transfer(self.ADDRESS, [write_message, read_message])

        return list(read_message.data)

    def close(self) -> None:
        self.i2c.close()
        self.imu_reset_gpio.close()

    def reset(self) -> None:
        self.imu_reset_gpio.write(True)
        sleep(self.RESET_TIMEOUT)
        self.imu_reset_gpio.write(False)
        _logger.info('Resetting BNO055')

    def reset2(self) -> None:
        self.write(Register.SYS_TRIG, 0x20)
        sleep(self.RESET_TIMEOUT)
        _logger.info('Resetting (2) BNO055')

    @property
    def acceleration_unit(self) -> Unit:
        return self._acceleration_unit

    @acceleration_unit.setter
    def acceleration_unit(self, value: Unit) -> None:
        self.select_units(
            value,
            self._angular_velocity_unit,
            self._angle_unit,
            self._temperature_unit,
        )

    @property
    def angular_velocity_unit(self) -> Unit:
        return self._angular_velocity_unit

    @angular_velocity_unit.setter
    def angular_velocity_unit(self, value: Unit) -> None:
        self.select_units(
            self._acceleration_unit,
            value,
            self._angle_unit,
            self._temperature_unit,
        )

    @property
    def angle_unit(self) -> Unit:
        return self._angle_unit

    @angle_unit.setter
    def angle_unit(self, value: Unit) -> None:
        self.select_units(
            self._acceleration_unit,
            self._angular_velocity_unit,
            value,
            self._temperature_unit,
        )

    @property
    def temperature_unit(self) -> Unit:
        return self._temperature_unit

    @temperature_unit.setter
    def temperature_unit(self, value: Unit) -> None:
        self.select_units(
            self._acceleration_unit,
            self._angular_velocity_unit,
            self._angle_unit,
            value,
        )

    def select_units(
            self,
            acceleration_unit: Unit,
            angular_velocity_unit: Unit,
            angle_unit: Unit,
            temperature_unit: Unit,
    ) -> None:
        """Select unit.

        'Writing 0x00 into UNIT_SEL selects following:'
        'Acceleration: m/s^2'
        'Angular rate: dps'
        'Temp: Celcius'
        """
        self._acceleration_unit = acceleration_unit
        self._angular_velocity_unit = angular_velocity_unit
        self._angle_unit = angle_unit
        self._temperature_unit = temperature_unit
        raw_units = (
            acceleration_unit
            | angular_velocity_unit
            | angle_unit
            | temperature_unit
        )

        self.write(Register.UNIT_SEL, raw_units)
        _logger.info(f'units set {bin(raw_units)[2:]}')

    @property
    def raw_units(self) -> int:
        return self.read(Register.UNIT_SEL, 1)[0]

    @property
    def raw_mode(self) -> int:
        return self.read(Register.OPR_MODE, 1)[0] & 0x0F

    def _get_vector(
            self,
            x_msb_register: Register,
            x_lsb_register: Register,
            y_msb_register: Register,
            y_lsb_register: Register,
            z_msb_register: Register,
            z_lsb_register: Register,
            representation: float,
    ) -> Vector:
        x_msb = self.read(x_msb_register, 1)
        x_lsb = self.read(x_lsb_register, 1)
        y_msb = self.read(y_msb_register, 1)
        y_lsb = self.read(y_lsb_register, 1)
        z_msb = self.read(z_msb_register, 1)
        z_lsb = self.read(z_lsb_register, 1)

        x = (x_msb[0] << 8) | x_lsb[0]
        y = (y_msb[0] << 8) | y_lsb[0]
        z = (z_msb[0] << 8) | z_lsb[0]

        if x & (1 << 15):
            x -= 1 << 16

        if y & (1 << 15):
            y -= 1 << 16

        if z & (1 << 15):
            z -= 1 << 16

        return self.Vector(
            x / representation,
            y / representation,
            z / representation,
        )

    ACCELERATION_UNIT_REPRESENTATIONS: ClassVar[dict[Unit, int]] = {
        Unit.MS2: 100,
        Unit.MG: 1,
    }

    @property
    def acceleration_unit_representation(self) -> int:
        return self.ACCELERATION_UNIT_REPRESENTATIONS[self.acceleration_unit]

    @property
    def acceleration(self) -> Vector:
        return self._get_vector(
            Register.ACC_DATA_X_MSB,
            Register.ACC_DATA_X_LSB,
            Register.ACC_DATA_Y_MSB,
            Register.ACC_DATA_Y_LSB,
            Register.ACC_DATA_Z_MSB,
            Register.ACC_DATA_Z_LSB,
            self.acceleration_unit_representation,
        )

    MAGNETIC_FIELD_UNIT_REPRESENTATION: ClassVar[int] = 16

    @property
    def magnetic_field(self) -> Vector:
        return self._get_vector(
            Register.MAG_DATA_X_MSB,
            Register.MAG_DATA_X_LSB,
            Register.MAG_DATA_Y_MSB,
            Register.MAG_DATA_Y_LSB,
            Register.MAG_DATA_Z_MSB,
            Register.MAG_DATA_Z_LSB,
            self.MAGNETIC_FIELD_UNIT_REPRESENTATION,
        )

    ANGULAR_VELOCITY_UNIT_REPRESENTATIONS: ClassVar[dict[Unit, int]] = {
        Unit.DPS: 16,
        Unit.RPS: 900,
    }

    @property
    def angular_velocity_unit_representation(self) -> int:
        unit = self.angular_velocity_unit

        return self.ANGULAR_VELOCITY_UNIT_REPRESENTATIONS[unit]

    @property
    def angular_velocity(self) -> Vector:
        return self._get_vector(
            Register.GYR_DATA_X_MSB,
            Register.GYR_DATA_X_LSB,
            Register.GYR_DATA_Y_MSB,
            Register.GYR_DATA_Y_LSB,
            Register.GYR_DATA_Z_MSB,
            Register.GYR_DATA_Z_LSB,
            self.angular_velocity_unit_representation,
        )

    ANGLE_UNIT_REPRESENTATIONS: ClassVar[dict[Unit, int]] = {
        Unit.DPS: 16,
        Unit.RPS: 900,
    }

    @property
    def angle_unit_representation(self) -> int:
        return self.ANGLE_UNIT_REPRESENTATIONS[self.angle_unit]

    @property
    def orientation(self) -> Vector:
        """Orientation (i.e., Euler angles).

        :return: The orientation vector.
        """
        return self._get_vector(
            Register.EUL_DATA_X_MSB,
            Register.EUL_DATA_X_LSB,
            Register.EUL_DATA_Y_MSB,
            Register.EUL_DATA_Y_LSB,
            Register.EUL_DATA_Z_MSB,
            Register.EUL_DATA_Z_LSB,
            self.angle_unit_representation,
        )

    QUATERNION_REPRESENTATION: ClassVar[int] = 1 << 14

    @property
    def quaternion(self) -> Quaternion:
        data_w_msb = self.read(Register.QUA_DATA_W_MSB, 1)
        data_w_lsb = self.read(Register.QUA_DATA_W_LSB, 1)
        data_x_msb = self.read(Register.QUA_DATA_X_MSB, 1)
        data_x_lsb = self.read(Register.QUA_DATA_X_LSB, 1)
        data_y_msb = self.read(Register.QUA_DATA_Y_MSB, 1)
        data_y_lsb = self.read(Register.QUA_DATA_Y_LSB, 1)
        data_z_msb = self.read(Register.QUA_DATA_Z_MSB, 1)
        data_z_lsb = self.read(Register.QUA_DATA_Z_LSB, 1)

        w = (data_w_msb[0] << 8) | data_w_lsb[0]
        x = (data_x_msb[0] << 8) | data_x_lsb[0]
        y = (data_y_msb[0] << 8) | data_y_lsb[0]
        z = (data_z_msb[0] << 8) | data_z_lsb[0]

        if w & (1 << 15):
            w -= 1 << 16

        if x & (1 << 15):
            x -= 1 << 16

        if y & (1 << 15):
            y -= 1 << 16

        if z & (1 << 15):
            z -= 1 << 16

        return self.Quaternion(
            w / self.QUATERNION_REPRESENTATION,
            x / self.QUATERNION_REPRESENTATION,
            y / self.QUATERNION_REPRESENTATION,
            z / self.QUATERNION_REPRESENTATION,
        )

    @property
    def linear_acceleration(self) -> Vector:
        return self._get_vector(
            Register.LIA_DATA_X_MSB,
            Register.LIA_DATA_X_LSB,
            Register.LIA_DATA_Y_MSB,
            Register.LIA_DATA_Y_LSB,
            Register.LIA_DATA_Z_MSB,
            Register.LIA_DATA_Z_LSB,
            self.acceleration_unit_representation,
        )

    @property
    def gravity(self) -> Vector:
        return self._get_vector(
            Register.GRV_DATA_X_MSB,
            Register.GRV_DATA_X_LSB,
            Register.GRV_DATA_Y_MSB,
            Register.GRV_DATA_Y_LSB,
            Register.GRV_DATA_Z_MSB,
            Register.GRV_DATA_Z_LSB,
            self.acceleration_unit_representation,
        )

    TEMPERATURE_UNIT_REPRESENTATIONS: ClassVar[dict[Unit, int]] = {
        Unit.CELSIUS: 1,
        Unit.FAHRENHEIT: 2,
    }

    @property
    def temperature_unit_representation(self) -> int:
        return self.TEMPERATURE_UNIT_REPRESENTATIONS[self.temperature_unit]

    @property
    def temperature(self) -> float:
        temperature = self.read(Register.TEMP, 1)[0]

        if temperature & (1 << 7):
            temperature -= 1 << 8

        return temperature / self.temperature_unit_representation

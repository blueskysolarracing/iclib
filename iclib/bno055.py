"""This module implements the BNO055 driver"""

from periphery import I2C, GPIO
from enum import IntEnum
from dataclasses import dataclass
import logging

_logger = logging.getLogger(__name__)


class Register(IntEnum):
    CHIP_ID = 0x00
    "Chip Identification Code"
    ACC_ID = 0x01
    """Chip ID of accelerometer Device"""
    MAG_ID = 0x02
    """Chip ID of magnetometer Device"""
    GYR_ID = 0x03
    """Chip ID of gyroscope device"""
    SW_REV_ID_LSB = 0x04
    """Lower Byte of SW Revision ID"""
    SW_REV_ID_MSB = 0x05
    """Upper Byte of SW Revision ID"""
    BL_REV_ID = 0x06
    """Identifies the version of the bootloader in the microcontroller"""
    PAGE_ID = 0x07
    """Number of currently selected page"""
    ACC_DATA_X_LSB = 0x08
    """Lower byte of x-axis acceleration data"""
    ACC_DATA_X_MSB = 0x09
    """Upper byte of x-axis acceleration data"""
    ACC_DATA_Y_LSB = 0x0A
    """Lower byte of Y axis acceleration data"""
    ACC_DATA_Y_MSB = 0x0B
    """Upper byte of y-axis acceleration data"""
    ACC_DATA_Z_LSB = 0x0C
    """Lower byte of z-axis acceleration data"""
    ACC_DATA_Z_MSB = 0x0D
    """Upper byte of z-axis acceleration data"""
    MAG_DATA_X_LSB = 0x0E
    """Lower byte of x-axis magnetometer data"""
    MAG_DATA_X_MSB = 0x0F
    """Upper byte of x-axis magnetometer data"""
    MAG_DATA_Y_LSB = 0x10
    """Lower byte of y-axis magnetometer data"""
    MAG_DATA_Y_MSB = 0x11
    """Upper byte of y-axis magnetometer data"""
    MAG_DATA_Z_LSB = 0x12
    """Lower byte of z-axis magnetometer data"""
    MAG_DATA_Z_MSB = 0x13
    """Upper byte of z-axis magnetometer data"""
    GYR_DATA_X_LSB = 0x14
    """Lower byte of x-axis gyroscope data"""
    GYR_DATA_X_MSB = 0x15
    """Upper byte of x-axis gyroscope data"""
    GYR_DATA_Y_LSB = 0x16
    """Lower byte of y-axis gyroscope data"""
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


@dataclass
class Operation_Modes(IntEnum):
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

    ms2 = 0x0
    mg = 0x1

    DPS = 0x0
    RPS = 0x2

    Degrees = 0x0
    Radians = 0x4

    C = 0x0
    F = 0x10


@dataclass
class BNO055:

    i2c: I2C
    gpio_out_imu_reset: GPIO

    ADDRESS = 0x28
    i2c_address: str
    gpio_address: str
    gpio_line: int
    com_direction: str

    @dataclass
    class Data_Return:
        @dataclass
        class Acceleration_Data:
            x: float
            y: float
            z: float

        @dataclass
        class Gyro_Data:
            x: float
            y: float
            z: float

        @dataclass
        class Quaternion_Data:
            x: int
            w: int
            z: int

        acceleration: type[Acceleration_Data]
        quaternion: type[Quaternion_Data]
        gyro: type[Gyro_Data]
        temperature: int

    def __post_init__(self) -> None:
        logging.basicConfig(level=logging.INFO)
        _logger = logging.getLogger(__name__)
        self.i2c = I2C(self.i2c_address)
        """original testing i2c_address: /dev/i2c-3"""

        if self.com_direction != "out":
            _logger.error("incorrect direction: should be set out")
            raise

        self.gpio_out_imu_reset = GPIO(self.gpio_address, self.com_direction)
        """original testing gpio_address: /dev/gpiochip4"""

    def operation_mode_sel(self, accel: bool, gyro: bool, mag: bool) -> None:
        if (accel is True and gyro is True and mag is True):
            self.write(Register.OPR_MODE, Operation_Modes.AMG)

        elif (accel is True and gyro is True):
            self.write(Register.OPR_MODE, Operation_Modes.ACCGYRO)

        elif (accel is True and mag is True):
            self.write(Register.OPR_MODE, Operation_Modes.ACCMAG)

        elif (mag is True and gyro is True):
            self.write(Register.OPR_MODE, Operation_Modes.MAGGYRO)

        elif (accel is True):
            self.write(Register.OPR_MODE, Operation_Modes.ACCONLY)

        elif (gyro is True):
            self.write(Register.OPR_MODE, Operation_Modes.GYROONLY)

        elif (mag is True):
            self.write(Register.OPR_MODE, Operation_Modes.MAGONLY)

        _logger.info("operation mode set")
        # write this for NDOF mode: 0x0C

    def write(self, register: Register, data: int) -> None:
        try:
            msg = I2C.Message([register, data], read=False)
            self.i2c.transfer(self.ADDRESS, [msg])
        except IOError as e:
            _logger.error(f"I2C write error: {e}")
            raise

    def read(self, register: Register,
             length: int) -> list[int]:
        try:
            read_msg = I2C.Message(bytearray(length), read=True)
            self.i2c.transfer(self.ADDRESS, [read_msg])
            return list(read_msg.data)
        except IOError as e:
            _logger.error(f"I2C read error: {e}")
            raise

    def close(self) -> None:
        self.i2c.close()
        self.gpio_out_imu_reset.close()

    def reset(self) -> None:
        self.gpio_out_imu_reset.write(False)
        self.gpio_out_imu_reset.write(True)
        _logger.info("reset")

    def set_units(
            self,
            accel_unit: int,
            ang_rate: int,
            euler_ang: int,
            temp: int
            ) -> None:
        "Writing 0x00 into UNIT_SEL selects following:"
        "Acceleration: m/s^2"
        "Angular rate: dps"
        "Temp: Celcius"
        if (temp == 0):
            temp_reg = Operation_Modes.C
        elif (temp == 1):
            temp_reg = Operation_Modes.F
        else:
            _logger.info("Temperature unit set error")

        if (euler_ang == 0):
            euler_reg = Operation_Modes.Degrees
        elif (euler_ang == 1):
            euler_reg = Operation_Modes.Radians
        else:
            _logger.info("Euler Angle unit set error")

        if (ang_rate == 0):
            rate_reg = Operation_Modes.DPS
        elif (ang_rate == 1):
            rate_reg = Operation_Modes.RPS
        else:
            _logger.info("Angular rate unit set error")

        if (accel_unit == 0):
            accel_reg = Operation_Modes.ms2
        elif (accel_unit == 1):
            accel_reg = Operation_Modes.mg
        else:
            _logger.info("Temperature unit set error")

        input_reg = accel_reg or rate_reg or euler_reg or temp_reg
        self.write(Register.UNIT_SEL, input_reg)
        _logger.info("units set")

    def verify_config(self) -> None:
        mode = self.read(Register.OPR_MODE, 1)[0] & 0x0F
        """lower 4 bits of OPR_MODE_REG represent the mode"""
        units = self.read(Register.UNIT_SEL, 1)[0]
        _logger.info(f"Current mode: {mode}, Units config: {units}")

    def check_calibration(self) -> tuple[int, int, int, int]:
        calib_status = self.read(Register.CALIB_STAT, 1)[0]
        sys_calib = (calib_status >> 6) & 0x03
        gyro_calib = (calib_status >> 4) & 0x03
        accel_calib = (calib_status >> 2) & 0x03
        mag_calib = calib_status & 0x03
        _logger.info(
            (
             f'Calibration - Sys: {sys_calib}/3, '
             f'Gyro: {gyro_calib}/3, '
             f'Accel: {accel_calib}/3, '
             f'Mag: {mag_calib}/3'
            )
        )
        return (sys_calib, gyro_calib, accel_calib, mag_calib)

    def calibration_setup(
        self, accel: bool, gyro: bool, mag: bool,
        accel_unit: int, angle_rate_unit: int,
        euler_ang_unit: int, temp_unit: int
            ) -> tuple[int, int, int, int]:
        try:
            chip_id = self.read(Register.CHIP_ID, 8)
            _logger.info(f"chip id: {str(chip_id)}")
            self.operation_mode_sel(accel, gyro, mag)
            self.set_units(
                    accel_unit,
                    angle_rate_unit,
                    euler_ang_unit,
                    temp_unit
                )
            _logger.info(
                "Initialization complete. Waiting for calibration..."
            )
            calibration_status = self.check_calibration()
            _logger.info("Sensor fully calibrated and ready")
            return calibration_status
        except Exception as e:
            _logger.error(f"Initialization failed: {e}")
            raise

    def read_quaternion(self) -> type[Data_Return.Quaternion_Data]:
        data_w_lsb = self.read(Register.QUA_DATA_W_LSB, 1)
        data_w_msb = self.read(Register.QUA_DATA_W_MSB, 1)
        data_x_lsb = self.read(Register.QUA_DATA_X_LSB, 1)
        data_x_msb = self.read(Register.QUA_DATA_X_MSB, 1)
        data_z_lsb = self.read(Register.QUA_DATA_Z_LSB, 1)
        data_z_msb = self.read(Register.QUA_DATA_Z_MSB, 1)
        data_w_msb[0] = data_w_msb[0] * 256
        data_x_msb[0] = data_x_msb[0] * 256
        data_z_msb[0] = data_z_msb[0] * 256

        BNO055.Data_Return.Quaternion_Data.w = data_w_lsb[0] + data_w_msb[0]
        BNO055.Data_Return.Quaternion_Data.x = data_x_lsb[0] + data_x_msb[0]
        BNO055.Data_Return.Quaternion_Data.z = data_z_lsb[0] + data_z_msb[0]
        return (BNO055.Data_Return.Quaternion_Data)

    def read_temperature(self) -> int:
        temperature = self.read(Register.TEMP, 1)
        return temperature[0]

    def read_acceleration(self) -> type[Data_Return.Acceleration_Data]:
        accel_x_lsb = [
            x / 100.0 for x in self.read(Register.ACC_DATA_X_LSB, 1)
        ]
        accel_y_lsb = [
            x / 100.0 for x in self.read(Register.ACC_DATA_Y_LSB, 1)
        ]
        accel_z_lsb = [
            x / 100.0 for x in self.read(Register.ACC_DATA_Z_LSB, 1)
        ]
        accel_x_msb = [
            x / 100.0 for x in self.read(Register.ACC_DATA_X_MSB, 1)
        ]
        accel_y_msb = [
            x / 100.0 for x in self.read(Register.ACC_DATA_Y_MSB, 1)
        ]
        accel_z_msb = [
            x / 100.0 for x in self.read(Register.ACC_DATA_Z_MSB, 1)
        ]
        accel_x_msb[0] = accel_x_msb[0] * 256
        accel_y_msb[0] = accel_y_msb[0] * 256
        accel_z_msb[0] = accel_z_msb[0] * 256

        BNO055.Data_Return.Acceleration_Data.x = (
            accel_x_msb[0] +
            accel_x_lsb[0]
            )
        BNO055.Data_Return.Acceleration_Data.y = (
            accel_y_msb[0] +
            accel_y_lsb[0]
            )
        BNO055.Data_Return.Acceleration_Data.z = (
            accel_z_msb[0] +
            accel_z_lsb[0]
            )

        return (BNO055.Data_Return.Acceleration_Data)

    def read_gyro(self) -> type[Data_Return.Gyro_Data]:
        gyro_x_lsb = [
            x / 16.0 for x in self.read(Register.GYR_DATA_X_LSB, 1)
        ]
        gyro_y_lsb = [
            x / 16.0 for x in self.read(Register.GYR_DATA_Y_LSB, 1)
        ]
        gyro_z_lsb = [
            x / 16.0 for x in self.read(Register.GYR_DATA_Z_LSB, 1)
        ]
        gyro_x_msb = [
            x / 16.0 for x in self.read(Register.GYR_DATA_X_MSB, 1)
        ]
        gyro_y_msb = [
            x / 16.0 for x in self.read(Register.GYR_DATA_Y_MSB, 1)
        ]
        gyro_z_msb = [
            x / 16.0 for x in self.read(Register.GYR_DATA_Z_MSB, 1)
        ]

        gyro_x_msb[0] = gyro_x_msb[0] * 256
        gyro_y_msb[0] = gyro_y_msb[0] * 256
        gyro_z_msb[0] = gyro_z_msb[0] * 256

        BNO055.Data_Return.Gyro_Data.x = gyro_x_msb[0] + gyro_x_lsb[0]
        BNO055.Data_Return.Gyro_Data.y = gyro_y_msb[0] + gyro_y_lsb[0]
        BNO055.Data_Return.Gyro_Data.z = gyro_z_msb[0] + gyro_z_lsb[0]

        return (BNO055.Data_Return.Gyro_Data)

    @property
    def read_all_data(self) -> type[Data_Return]:
        """reads acceleration, quaternion, gyro, and temperature"""

        BNO055.Data_Return.acceleration = self.read_acceleration()
        BNO055.Data_Return.quaternion = self.read_quaternion()
        BNO055.Data_Return.gyro = self.read_gyro()
        BNO055.Data_Return.temperature = self.read_temperature()
        return (BNO055.Data_Return)

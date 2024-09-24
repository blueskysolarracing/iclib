"""This module implements the BNO055 driver"""

from periphery import I2C, GPIO
from enum import IntEnum
from dataclasses import dataclass
import logging

from iclib.utilities import twos_complement


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

    BNO055_ADDR = 0x28


@dataclass
class BNO055:

    i2c: I2C
    gpio_out_imu_reset: GPIO
    _logger: logging.Logger

    def initialize(self, i2c_address: str, gpio_address: str,
                   gpio_line: int) -> None:
        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger(__name__)
        self.i2c = I2C(i2c_address)
        """str: /dev/i2c-3 in original"""
        self.gpio_out_imu_reset = GPIO(gpio_address, gpio_line, "out")
        """/dev/gpiochip4"""

    def operation_mode_sel(self) -> None:
        self.write(Register.OPR_MODE, 0x0C)
        self._logger.info("operation mode set")
        """write this for NDOF mode: 0x0C"""

    def write(self, register: Register, data: int) -> None:
        try:
            msg = I2C.Message([register, data], read=False)
            self.i2c.transfer(Register.BNO055_ADDR, [msg])
        except IOError as e:
            self._logger.error(f"I2C write error: {e}")
            raise

    def read(self, register: Register,
             length: int) -> list[int]:
        try:
            read_msg = I2C.Message(bytearray(length), read=True)
            self.i2c.transfer(Register.BNO055_ADDR, [read_msg])
            return list(read_msg.data)
        except IOError as e:
            self._logger.error(f"I2C read error: {e}")
            raise

    def close(self) -> None:
        self.i2c.close()
        self.gpio_out_imu_reset.close()

    def reset(self) -> None:
        self.gpio_out_imu_reset.write(False)
        self.gpio_out_imu_reset.write(True)
        self._logger.info("reset")

    def set_units(self) -> None:
        """Writing 0x00 into UNIT_SEL selects following:"""
        """Acceleration: m/s^2"""
        """Angular rate: dps"""
        """Temp: Celcius"""
        self.write(Register.UNIT_SEL, 0x00)
        self._logger.info("units set")

    def verify_config(self) -> None:
        mode = self.read(Register.OPR_MODE, 1)[0] & 0x0F
        """lower 4 bits of OPR_MODE_REG represent the mode"""
        units = self.read(Register.UNIT_SEL, 1)[0]
        self._logger.info(f"Current mode: {mode}, Units config: {units}")

    def check_calibration(self) -> None:
        calib_status = self.read(Register.CALIB_STAT, 1)[0]
        sys_calib = (calib_status >> 6) & 0x03
        gyro_calib = (calib_status >> 4) & 0x03
        accel_calib = (calib_status >> 2) & 0x03
        mag_calib = calib_status & 0x03
        self._logger.info(
            f"Calibration - Sys: {sys_calib}/3, " +
            f"Gyro: {gyro_calib}/3, " +
            f"Accel: {accel_calib}/3, " +
            f"Mag: {mag_calib}/3"
        )

    @property
    def calibration_setup(self) -> None:
        try:
            chip_id = self.read(Register.CHIP_ID, 8)
            self._logger.info(f"chip id: {str(chip_id)}")
            self.operation_mode_sel()
            self.set_units()
            self._logger.info(
                "Initialization complete. Waiting for calibration..."
            )
            self.check_calibration()
            self._logger.info("Sensor fully calibrated and ready")
        except Exception as e:
            self._logger.error(f"Initialization failed: {str(e)}")
            raise

    def read_quaternion(self) -> list[int]:
        data_w_lsb = self.read(Register.QUA_DATA_W_LSB, 1)
        data_w_msb = self.read(Register.QUA_DATA_W_MSB, 1)
        data_x_lsb = self.read(Register.QUA_DATA_X_LSB, 1)
        data_x_msb = self.read(Register.QUA_DATA_X_MSB, 1)
        data_z_lsb = self.read(Register.QUA_DATA_Z_LSB, 1)
        data_z_msb = self.read(Register.QUA_DATA_Z_MSB, 1)
        data_w_msb[0] = data_w_msb[0] * 256
        data_x_msb[0] = data_x_msb[0] * 256
        data_z_msb[0] = data_z_msb[0] * 256
        return (
            [data_w_lsb[0] + data_w_msb[0],
             data_x_lsb[0] + data_w_msb[0],
             data_z_lsb[0] + data_z_msb[0]]
        )

    def read_temperature(self) -> list[int]:
        return self.read(Register.TEMP, 8)

    def read_acceleration(self) -> list[float]:
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
        return (
            [accel_x_msb[0] + accel_x_lsb[0],
             accel_y_msb[0] + accel_y_lsb[0],
             accel_z_msb[0] + accel_z_lsb[0]]
        )

    def read_gyro(self) -> list[float]:
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
        return (
            [gyro_x_msb[0] + gyro_x_lsb[0],
             gyro_y_msb[0] + gyro_y_lsb[0],
             gyro_z_msb[0] + gyro_z_lsb[0]]
        )

    @property
    def read_all_data(self) -> set[object]:
        """reads acceleration, quaternion, gyro, and temperature"""
        return {
            self.read_acceleration(),
            self.read_quaternion(),
            self.read_gyro(),
            self.read_temperature()
        }

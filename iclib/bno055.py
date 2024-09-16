#page 55 register map, power on is page 0 register map, can switch by toggling PAGE_ID register
#page 99 interface: select standard i2c interface ps1 0 (pin5), ps0 0 (pin6)
#page 100 i2c protocal: bno055 default i2c address when input pin com3 (pin 17) HIGH is 0x29, if LOW then 0x28


#additional
#axis remap if mounted not in default orientation,  offest to calibrate errors

#for calibration check out page 51

#questions:
#configure/check sda, scl on device tree?

#toradex pinout spreadsheet imu output: toradex pinout 203 SENSOR_I2C3_SDA, 201 SENSOR_I2C3_SCL
'''
i2c3_sda_pin = 203
i2c3_scl_pin = 201
'''

"""This module implements the BNO055 driver"""
     
from periphery import I2C, GPIO
from dataclasses import dataclass
from enum import IntEnum, Enum, auto
from time import sleep
import logging

from iclib.utilities import twos_complement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

i2c = I2C("/dev/i2c-3") #run i2cdetect -l to find available i2c bus, this case shoudl be 3? CONFIRM

class Register(IntEnum):
    CHIP_ID = 0x00
    "Chip Identification Code"
    ACC_ID= 0x01
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

    """
    BNO055_ADDR = 0x28 #COM3 is connected to ground
    OPR_MODE_REG = 0x3D #register for operation mode
    NDOF_MODE = 0x0C #
    UNIT_SEL_REG = 0x3B
    UNIT_MODE = 0x00
    ACC_DATA_X_LSB = 0x08
    MAG_DATA_X_LSB = 0x0E
    GYR_DATA_X_LSB = 0x14
    EUL_DATA_X_LSB = 0x1A
    QUA_DATA_W_LSB = 0x20
    LIA_DATA_X_LSB = 0x28
    GRV_DATA_X_LSB = 0x2E
    TEMP = 0x34
    CALIB_STAT_REG = 0x35
    """
    def __init__(self, address: int, name: str, size: int) -> None:
        self.address = address
        self.__name = name
        self.size = size



gpio_out_imu_reset = GPIO("/dev/gpiochip4",21,"out") #SENSOR_IMU_RST pin on toradex


class BNO055:



    def write(self, register: Register, data) -> int:
        try:
            msg = I2C.Message([register, data], read=False)
            i2c.transfer(BNO055_ADDR, [msg])
        except IOError as e:
            logger.error(f"I2C write error: {e}")
            raise

    def read(self, register: Register, length=1) -> int:
        try:
            write_msg = I2C.Message([register], read=False)
            read_msg = I2C.Message([0x00]*length, read=True)
            i2c.transfer(BNO055_ADDR, [write_msg, read_msg])
            return read_msg.data
        except IOError as e:
            logger.error(f"I2C read error: {e}")
            raise

    def close(self):
        i2c.close()
        gpio_out_imu_reset.close()


    def reset(self):
        gpio_out_imu_reset.write(False)
        sleep(0.05)
        gpio_out_imu_reset.write(True)
        logger.info("reset")

    @property
    def set_op_mode(self):
        #page 22 for all possible operation modes
        self.write(Register.OPR_MODE, NDOF_MODE)
        sleep(0.05)
        logger.info("operation mode set")

    @property
    def set_units(self):
        # Set acceleration to m/s^2, angular rate to dps, Euler angles to degrees, temp to Celsius
        self.write(Register.UNIT_SEL, Register.UNIT_MODE)
        sleep(0.05)
        logger.info("units set")

    @property
    def verify_config(self):
        mode = self.read(Register.OPR_MODE, 1)[0] & 0x0F #lower 4 bits of OPR_MODE_REG represent the mode
        units = self.read(Register.UNIT_SEL, 1)[0] 
        logger.info(f"Current mode: {mode}, Units config: {units}")
        return mode == NDOF_MODE and units == UNIT_MODE

    @property
    def check_calibration(self):
        calib_status = self.read(Register.CALIB_STAT, 1)[0]
        sys_calib = (calib_status >> 6) & 0x03
        gyro_calib = (calib_status >> 4) & 0x03
        accel_calib = (calib_status >> 2) & 0x03
        mag_calib = calib_status & 0x03
        logger.info(f"Calibration - Sys: {sys_calib}/3, Gyro: {gyro_calib}/3, Accel: {accel_calib}/3, Mag: {mag_calib}/3")
        return sys_calib == 3 and gyro_calib == 3 and accel_calib == 3 and mag_calib == 3
        
    @property
    def initialize(self):
        try:
            self.reset()
            sleep(0.1)  # Wait for reset to complete
            chip_id = self.read(0x00)
            logger.info(f"chip id: {str(chip_id)}")
            self.set_op_mode()
            self.set_units()
            if not self.verify_config():
                raise Exception("Failed to set correct mode or units")
            logger.info("Initialization complete. Waiting for calibration...")
            while not self.check_calibration():
                sleep(1)
            logger.info("Sensor fully calibrated and ready")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise
            
    """
    def twos_comp(val, bits=16):
        if val & (1 << (bits - 1)):
            val -= (1 << bits)
        return val
    """
    @property
    def read_vector(self, register):
        data = self.read(register, 6)
        return [
            twos_complement((data[1] << 8) | data[0]),
            twos_complement((data[3] << 8) | data[2]),
            twos_complement((data[5] << 8) | data[4])
        ]


    """question abt 2s complement"""
    @property
    def read_quaternion(self):
        data_w_lsb = self.read(Register.QUA_DATA_W_LSB, 8)
        data_w_msb = self.read(Register.QUA_DATA_W_MSB, 8)
        data_x_lsb = self.read(Register.QUA_DATA_X_LSB, 8)
        data_x_msb = self.read(Register.QUA_DATA_X_MSB, 8)
        data_z_lsb = self.read(Register.QUA_DATA_Z_LSB, 8)
        data_z_msb = self.read(Register.QUA_DATA_Z_MSB, 8)
        return [
            twos_complement((data[1] << 8) | data[0]),
            twos_complement((data[3] << 8) | data[2]),
            twos_complement((data[5] << 8) | data[4]),
            twos_complement((data[7] << 8) | data[6])
        ]

    @property
    def read_temperature(self):
        return self.read_register(Register.TEMP)[0]
    

    """should i return number or list"""
    @property
    def read_acceleration(self):
        accel_x_lsb = [x / 100.0 for x in self.read_vector(Register.ACC_DATA_X_LSB)] #1m/s^2 = 100 lsb
        accel_y_lsb = [x / 100.0 for x in self.read_vector(Register.ACC_DATA_Y_LSB)]
        accel_z_lsb = [x / 100.0 for x in self.read_vector(Register.ACC_DATA_Z_LSB)]
        accel_x_msb = [x / 100.0 for x in self.read_vector(Register.ACC_DATA_X_MSB)] #1m/s^2 = 100 lsb
        accel_y_msb = [x / 100.0 for x in self.read_vector(Register.ACC_DATA_Y_MSB)]
        accel_z_msb = [x / 100.0 for x in self.read_vector(Register.ACC_DATA_Z_MSB)]

        return{[accel_x_msb, accel_x_lsb], [accel_y_msb, accel_y_lsb], [accel_z_msb, accel_z_lsb]}

    @property
    def read_gyro(self):
        gyro_x_lsb = [x / 16.0 for x in self.read_vector(Register.GYR_DATA_X_LSB)]
        gyro_y_lsb = [x / 16.0 for x in self.read_vector(Register.GYR_DATA_Y_LSB)]
        gyro_z_lsb = [x / 16.0 for x in self.read_vector(Register.GYR_DATA_Z_LSB)]
        gyro_x_msb = [x / 16.0 for x in self.read_vector(Register.GYR_DATA_X_MSB)]
        gyro_y_msb = [x / 16.0 for x in self.read_vector(Register.GYR_DATA_Y_MSB)]
        gyro_z_msb = [x / 16.0 for x in self.read_vector(Register.GYR_DATA_Z_MSB)]

        return{[gyro_x_msb, gyro_x_lsb], [gyro_y_msb, gyro_y_lsb], [gyro_z_msb, gyro_z_lsb]}


    @property
    def read_all_data(self):
        """
        accel_x = [x / 100.0 for x in self.read_vector(Register.ACC_DATA_X_LSB)] #1m/s^2 = 100 lsb
        mag_x = [x / 16.0 for x in self.read_vector(MAG_DATA_X_LSB)] #1uT = 16 lsb
        gyro_x = [x / 16.0 for x in self.read_vector(GYR_DATA_X_LSB)] #1dps = 16 lsb
        euler = [x / 16.0 for x in read_vector(EUL_DATA_X_LSB)] #1 degree = 16 lsb
        quat = [x / (1 << 14) for x in read_quaternion()] #1 LSB = 1/16384
        lia = [x / 100.0 for x in read_vector(LIA_DATA_X_LSB)] #1m/s^2 = 100 lsb    
        grv = [x / 100.0 for x in read_vector(GRV_DATA_X_LSB)] #1m/s^2 = 100 lsb
        temp = read_temperature() #1 degree = 1 lsb

        return {
            'acceleration': accel,
            'magnetometer': mag,
            'gyroscope': gyro,
            'euler': euler,
            'quaternion': quat,
            'linear_acceleration': lia,
            'gravity': grv,
            'temperature': temp
        }
        """
        return{self.read_acceleration(), self.read_quaternion(), self.read_gyro()}

def main():
    try:
        BNO055.initialize()
        while True:
            data = BNO055.read_all_data()
            print("Acceleration (m/s^2):", data['acceleration'])
            print("Magnetometer (uT):", data['magnetometer'])
            print("Gyroscope (dps):", data['gyroscope'])
            print("Euler Angles (degrees):", data['euler'])
            print("Quaternion:", data['quaternion'])
            print("Linear Acceleration (m/s^2):", data['linear_acceleration'])
            print("Gravity Vector (m/s^2):", data['gravity'])
            print("Temperature (°C):", data['temperature'])
            print("--------------------")
            sleep(0.1)
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print("Error:", str(e))
    finally:
        i2c.close()
        gpio_out_imu_reset.close()

if __name__ == "__main__":
    main()

#https://python-periphery.readthedocs.io/en/latest/i2c.html  #function information
#https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bno055-ds000.pdf #tells read/write,register information
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

"""This Module """
     
from periphery import I2C, GPIO
from time import sleep
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

i2c = I2C("/dev/i2c-3") #run i2cdetect -l to find available i2c bus, this case shoudl be 3? CONFIRM





gpio_out_imu_reset = GPIO("/dev/gpiochip4",21,"out") #SENSOR_IMU_RST pin on toradex
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




def write_register(register, data):
    try:
        msg = I2C.Message([register, data], read=False)
        i2c.transfer(BNO055_ADDR, [msg])
    except IOError as e:
        logger.error(f"I2C write error: {e}")
        raise

def read_register(register, length=1):
    try:
        write_msg = I2C.Message([register], read=False)
        read_msg = I2C.Message([0x00]*length, read=True)
        i2c.transfer(BNO055_ADDR, [write_msg, read_msg])
        return read_msg.data
    except IOError as e:
        logger.error(f"I2C read error: {e}")
        raise


def close():
    i2c.close()
    gpio_out_imu_reset.close()


def reset():
    gpio_out_imu_reset.write(False)
    sleep(0.05)
    gpio_out_imu_reset.write(True)
    logger.info("reset")


def set_op_mode():
    #page 22 for all possible operation modes
    write_register(OPR_MODE_REG, NDOF_MODE)
    sleep(0.05)
    logger.info("operation mode set")

def set_units():
    # Set acceleration to m/s^2, angular rate to dps, Euler angles to degrees, temp to Celsius
    write_register(UNIT_SEL_REG, UNIT_MODE)
    sleep(0.05)
    logger.info("units set")

def verify_config():
    mode = read_register(OPR_MODE_REG, 1)[0] & 0x0F #lower 4 bits of OPR_MODE_REG represent the mode
    units = read_register(UNIT_SEL_REG, 1)[0] 
    logger.info(f"Current mode: {mode}, Units config: {units}")
    return mode == NDOF_MODE and units == UNIT_MODE

def check_calibration():
    calib_status = read_register(CALIB_STAT_REG, 1)[0]
    sys_calib = (calib_status >> 6) & 0x03
    gyro_calib = (calib_status >> 4) & 0x03
    accel_calib = (calib_status >> 2) & 0x03
    mag_calib = calib_status & 0x03
    logger.info(f"Calibration - Sys: {sys_calib}/3, Gyro: {gyro_calib}/3, Accel: {accel_calib}/3, Mag: {mag_calib}/3")
    return sys_calib == 3 and gyro_calib == 3 and accel_calib == 3 and mag_calib == 3
    
def initialize():
    try:
        reset()
        sleep(0.1)  # Wait for reset to complete
        chip_id = read_register(0x00)
        logger.info(f"chip id: {str(chip_id)}")
        set_op_mode()
        set_units()
        if not verify_config():
            raise Exception("Failed to set correct mode or units")
        logger.info("Initialization complete. Waiting for calibration...")
        while not check_calibration():
            sleep(1)
        logger.info("Sensor fully calibrated and ready")
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        raise
            

def twos_comp(val, bits=16):
    if val & (1 << (bits - 1)):
        val -= (1 << bits)
    return val

def read_vector(register):
    data = read_register(register, 6)
    return [
        twos_comp((data[1] << 8) | data[0]),
        twos_comp((data[3] << 8) | data[2]),
        twos_comp((data[5] << 8) | data[4])
    ]

def read_quaternion():
    data = read_register(QUA_DATA_W_LSB, 8)
    return [
        twos_comp((data[1] << 8) | data[0]),
        twos_comp((data[3] << 8) | data[2]),
        twos_comp((data[5] << 8) | data[4]),
        twos_comp((data[7] << 8) | data[6])
    ]

def read_temperature():
    return read_register(TEMP)[0]

def read_all_data():
    accel = [x / 100.0 for x in read_vector(ACC_DATA_X_LSB)] #1m/s^2 = 100 lsb
    mag = [x / 16.0 for x in read_vector(MAG_DATA_X_LSB)] #1uT = 16 lsb
    gyro = [x / 16.0 for x in read_vector(GYR_DATA_X_LSB)] #1dps = 16 lsb
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

def main():
    try:
        initialize()
        while True:
            data = read_all_data()
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
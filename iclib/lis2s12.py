
from dataclasses import dataclass, field
from enum import IntEnum
from logging import getLogger
from time import sleep
from typing import ClassVar

from periphery import I2C, GPIO


class Register(IntEnum):
    SENSORHUB1_REG = 0x06
    SENSORHUB2_REG = 0x07
    SENSORHUB3_REG = 0x08
    SENSORHUB4_REG = 0x09
    SENSORHUB5_REG = 0x0A
    SENSORHUB6_REG = 0x0B
    """Sensor hub output registers for external sensor data."""
    
    MODULE_8BIT = 0x0C
    """Module output value register."""
    
    WHO_AM_I = 0x0F
    """Device identification register."""
    
    CTRL1 = 0x20
    CTRL2 = 0x21
    CTRL3 = 0x22
    CTRL4 = 0x23
    CTRL5 = 0x24
    """Control registers for device configuration and interrupt settings."""
    
    FIFO_CTRL = 0x25
    """FIFO control register."""
    
    OUT_T = 0x26
    """Temperature sensor output register."""
    
    STATUS = 0x27
    """Status register for data ready and event flags."""
    
    OUT_X_L = 0x28
    OUT_X_H = 0x29
    OUT_Y_L = 0x2A
    OUT_Y_H = 0x2B
    OUT_Z_L = 0x2C
    OUT_Z_H = 0x2D
    """Acceleration data output registers (X, Y, Z axes, LSB and MSB)."""
    
    FIFO_THS = 0x2E
    FIFO_SRC = 0x2F
    FIFO_SAMPLES = 0x30
    """FIFO threshold, status, and sample count registers."""
    
    TAP_6D_THS = 0x31
    INT_DUR = 0x32
    WAKE_UP_THS = 0x33
    WAKE_UP_DUR = 0x34
    FREE_FALL = 0x35
    """Threshold and duration configuration registers for motion detection."""
    
    STATUS_DUP = 0x36
    WAKE_UP_SRC = 0x37
    TAP_SRC = 0x38
    SIX_D_SRC = 0x39
    """Event detection status and source registers."""
    
    STEP_COUNTER_MINTHS = 0x3A
    STEP_COUNTER_L = 0x3B
    STEP_COUNTER_H = 0x3C
    """Step counter configuration and output registers."""
    
    FUNC_CK_GATE = 0x3D
    FUNC_SRC = 0x3E
    FUNC_CTRL = 0x3F
    """Embedded function control and status registers."""


class OutputDataRate(IntEnum):
    POWER_DOWN = 0x0
    ODR_1_HZ = 0x8
    ODR_12_5_HZ = 0x9
    ODR_25_HZ = 0xA
    ODR_50_HZ = 0xB
    ODR_100_HZ = 0xC
    ODR_200_HZ = 0xD
    ODR_400_HZ = 0xE
    ODR_800_HZ = 0xF
    ODR_12_5_HZ_HR = 0x1
    ODR_25_HZ_HR = 0x2
    ODR_50_HZ_HR = 0x3
    ODR_100_HZ_HR = 0x4
    ODR_200_HZ_HR = 0x5
    ODR_400_HZ_HR = 0x6
    ODR_800_HZ_HR = 0x7
    ODR_1600_HZ = 0x5
    ODR_3200_HZ = 0x6
    ODR_6400_HZ = 0x7

class FullScale(IntEnum):
    FS_2G = 0x0
    FS_16G = 0x1
    FS_4G = 0x2
    FS_8G = 0x3


@dataclass
class LIS2DS12:
    ADDRESS: ClassVar[int] = 0x1E 
    DEVICE_ID: ClassVar[int] = 0x43
    
    i2c: I2C
    
    @dataclass
    class Vector:
        x: float
        y: float
        z: float

    def __post_init__(self) -> None:


        if self.DEVICE_ID != self.read(Register.WHO_AM_I, 1)[0]:
            raise ValueError('Incorrect Device ID')


    def write(self, register: Register, data: int) -> None:
        message = I2C.Message([register, data])

        self.i2c.transfer(self.ADDRESS, [message])

    def read(self, register: Register, length: int) -> list[int]:
        write_message = I2C.Message([register])
        read_message = I2C.Message([0] * length, read=True)

        self.i2c.transfer(self.ADDRESS, [write_message, read_message])

        return list(read_message.data)
        
    def configure(self, odr: OutputDataRate = OutputDataRate.ODR_100_HZ,
              full_scale: FullScale = FullScale.FS_2G,
              high_resolution: bool = True) -> None:

        ctrl1_value = 0x00

       
        if odr in [OutputDataRate.ODR_12_5_HZ_HR, OutputDataRate.ODR_25_HZ_HR,
                   OutputDataRate.ODR_50_HZ_HR, OutputDataRate.ODR_100_HZ_HR,
                   OutputDataRate.ODR_200_HZ_HR, OutputDataRate.ODR_400_HZ_HR,
                   OutputDataRate.ODR_800_HZ_HR]:
            
            ctrl1_value |= (odr.value << 4)
            high_resolution = True  
        elif odr in [OutputDataRate.ODR_1600_HZ, OutputDataRate.ODR_3200_HZ,
                     OutputDataRate.ODR_6400_HZ]:
           
            ctrl1_value |= (odr.value << 4)
            ctrl1_value |= 0x02  
            high_resolution = False  
        else:
           
            ctrl1_value |= (odr.value << 4)

        ctrl1_value |= (full_scale.value << 2)

      
        ctrl1_value |= 0x01  # Set BDU bit

        self.write(Register.CTRL1, ctrl1_value)


        ctrl2_value = 0x00
        ctrl2_value |= 0x02  

      
        if high_resolution:
            ctrl2_value |= 0x08  

        self.write(Register.CTRL2, ctrl2_value)

       
        ctrl4_value = 0x00

        if high_resolution:
          
            ctrl4_value |= 0x00  
        else:
           
            ctrl4_value |= 0x40  

        self.write(Register.CTRL4, ctrl4_value)

      
        sleep(0.01)
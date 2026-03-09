"""This module implements the LIS2HH12 driver."""

from dataclasses import dataclass, field
from enum import IntEnum
import time

from periphery import GPIO, I2C

from iclib.utilities import twos_complement

class Register(IntEnum):
    TEMP_L = 0x0B
    TEMP_H = 0x0C
    WHO_AM_I = 0x0F
    ACT_THS = 0x1E
    ACT_DUR = 0x1F
    CTRL1 = 0x20
    CTRL2 = 0x21
    CTRL3 = 0x22
    CTRL4 = 0x23
    CTRL5 = 0x24
    CTRL6 = 0x25
    CTRL7 = 0x26
    STATUS = 0x27
    OUT_X_L = 0x28
    OUT_X_H = 0x29
    OUT_Y_L = 0x2A
    OUT_Y_H = 0x2B
    OUT_Z_L = 0x2C
    OUT_Z_H = 0x2D
    FIFO_CTRL = 0x2E
    FIFO_SRC = 0x2F
    IG_CFG1 = 0x30
    IG_SRC1 = 0x31
    IG_THS_X1 = 0x32
    IG_THS_Y1 = 0x33
    IG_THS_Z1 = 0x34
    IG_DUR1 = 0x35
    IG_CFG2 = 0x36
    IG_SRC2 = 0x37
    IG_THS2 = 0x38
    IG_DUR2 = 0x39
    XL_REFERENCE = 0x3A
    XH_REFERENCE = 0x3B
    YL_REFERENCE = 0x3C
    YH_REFERENCE = 0x3D
    ZL_REFERENCE = 0x3E
    ZH_REFERENCE = 0x3F

@dataclass
class LIS2HH12:
    """A Python driver for STMicroelectronics LIS2HH12 accelerometer"""
    
    i2c: I2C
    """The I2C bus."""
    sa0_pin: bool
    """The device version."""
    output_data_rate: int = field(init=False, default=0)
    measurement_range: int = field(init=False, default=2)
    address: int = field(init=False)
    """The address on I2C bus."""

    def __post_init__(self) -> None:
        if self.sa0_pin:
            self.address = 0b0011101
        else:
            self.address = 0b0011110
        # 6.1.1 I2C operation, page 24

    @dataclass
    class Vector:
        x: float
        y: float
        z: float

        def __add__(self, other: 'LIS2HH12.Vector') -> 'LIS2HH12.Vector':
            return LIS2HH12.Vector(
                self.x + other.x,
                self.y + other.y,
                self.z + other.z
            )

        def __sub__(self, other: 'LIS2HH12.Vector') -> 'LIS2HH12.Vector':
            return LIS2HH12.Vector(
                self.x - other.x,
                self.y - other.y,
                self.z - other.z
            )

        def __iter__(self):
            return iter((self.x, self.y, self.z))

    def write(self, register: Register, data: int) -> None:
        message = I2C.Message([register, data])

        self.i2c.transfer(self.address, [message])

    def write_bits(
        self,
        register: Register,
        bits: dict[int, bool]
    ) -> None:
        raw = self.read(register, 1)[0] & 0xFF

        for bit, value in bits.items():
            if value:
                raw |= 1 << bit
            else:
                raw &= ~(1 << bit)

        self.write(register, raw)

    def read(self, register: Register, length: int) -> list[int]:
        if length > 1:
            register |= 0x80

        write_message = I2C.Message([register])
        read_message = I2C.Message([0] * length, read=True)
        self.i2c.transfer(self.address, [write_message, read_message])

        return list(read_message.data)

    def close(self) -> None:
        self.i2c.close()

    def config(
            self,
            odr: int | None = None,
            measurement_range: int | None = None,
            enable_axes: bool = False,
            enable_auto_inc: bool = False,
    ) -> None:
        if odr is not None:
            if odr not in [0, 10, 50, 100, 200, 400, 800]:
                raise ValueError('invalid output data rate')

            match odr:
                case 0:
                    odr_bits = {6: 0, 5: 0, 4: 0}
                case 10:
                    odr_bits = {6: 0, 5: 0, 4: 1}
                case 50:
                    odr_bits = {6: 0, 5: 1, 4: 0}
                case 100:
                    odr_bits = {6: 0, 5: 1, 4: 1}
                case 200:
                    odr_bits = {6: 1, 5: 0, 4: 0}
                case 400:
                    odr_bits = {6: 1, 5: 0, 4: 1}
                case 800:
                    odr_bits = {6: 1, 5: 1, 4: 0}
            
            self.output_data_rate = odr
            self.write_bits(Register.CTRL1, odr_bits)
            # 8.5 CTRL1 (20h), page 31

        if measurement_range is not None:
            if measurement_range not in [2, 4, 8]:
                raise ValueError('invalid measurement range')
            
            match measurement_range:
                case 2:
                    range_bits = {5: 0, 4: 0}
                case 4:
                    range_bits = {5: 1, 4: 0}
                case 8:
                    range_bits = {5: 1, 4: 1}

            self.measurement_range = measurement_range
            self.write_bits(Register.CTRL4, range_bits) 
            # 8.8 CTRL4 (23h), page 34
        
        if enable_axes:
            self.write_bits(Register.CTRL1, {2: 1, 1: 1, 0: 1})
            # Enable all axes, 8.5 CTRL1 (20h), page 31

        if enable_auto_inc:
            self.write_bits(Register.CTRL4, {2: 1})
            # Enable auto increment, 8.8 CTRL4 (23h), page 34

    def read_temperature(self):
        raw = self.read(Register.TEMP_L, 2)
        raw_temp = twos_complement((raw[1] << 8 | raw[0]), 16)
        temp = 25.0 + raw_temp / 8.0
        return temp
        # 2.3 Temperature sensor characteristics, page 11

    def read_acceleration(self) -> 'LIS2HH12.Vector':
        raw = self.read(Register.OUT_X_L, 6)
        
        xg = (
            twos_complement((raw[1] << 8 | raw[0]), 16)
            * 0.0305 * self.measurement_range / 1000.0
        )
        yg = (
            twos_complement((raw[3] << 8 | raw[2]), 16)
            * 0.0305 * self.measurement_range / 1000.0
        )
        zg = (
            twos_complement((raw[5] << 8 | raw[4]), 16)
            * 0.0305 * self.measurement_range / 1000.0
        )

        return self.Vector(xg, yg, zg)
        # 2.1 Mechanical characteristics, page 10

    def self_test(self) -> bool:
        self.write_bits(Register.CTRL5, {3: 0, 2: 0})
        time.sleep(0.0125)
        before = self.read_acceleration()
        self.write_bits(Register.CTRL5, {3: 0, 2: 1})
        time.sleep(0.0125)
        pos = self.read_acceleration()
        self.write_bits(Register.CTRL5, {3: 1, 2: 0})
        time.sleep(0.0125)
        neg = self.read_acceleration()
        self.write_bits(Register.CTRL5, {3: 0, 2: 0})
        time.sleep(0.0125)

        pos_diff = pos - before
        neg_diff = before - neg

        print(f"Before: {before}, Pos: {pos}, Neg: {neg}")
        print(f"Pos Diff: {pos_diff}, Neg Diff: {neg_diff}")

        pos_test = all(0.07 <= i <= 1.5 for i in pos_diff)
        neg_test = all(0.07 <= i <= 1.5 for i in neg_diff)

        return pos_test and neg_test
        # 2.1 Mechanical characteristics, pahe 10
        # 2.6.3 Self-test, page 15
        # 8.9 CTRL5 (24h), page 35
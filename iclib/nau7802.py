"""This module implements the NAU7802 driver."""

from dataclasses import dataclass
from enum import Enum, IntEnum
from time import sleep
from typing import cast, ClassVar

from periphery import GPIO, I2C


class Register(IntEnum):
    PU_CTRL = 0x00
    CTRL1 = 0x01
    CTRL2 = 0x02
    OCAL1_B2 = 0x03
    OCAL1_B1 = 0x04
    OCAL1_B0 = 0x05
    GCAL1_B3 = 0x06
    GCAL1_B2 = 0x07
    GCAL1_B1 = 0x08
    GCAL1_B0 = 0x09
    OCAL2_B2 = 0x0A
    OCAL2_B1 = 0x0B
    OCAL2_B0 = 0x0C
    GCAL2_B3 = 0x0D
    GCAL2_B2 = 0x0E
    GCAL2_B1 = 0x0F
    GCAL2_B0 = 0x10
    I2C_CTRL = 0x11
    ADCO_B2 = 0x12
    ADCO_B1 = 0x13
    ADCO_B0 = 0x14
    OTP_B1 = 0x15
    OTP_B0 = 0x16


class RegisterBit(tuple[Register, int], Enum):
    PU_CTRL_AVDDS = Register.PU_CTRL, 7
    PU_CTRL_OSCS = Register.PU_CTRL, 6
    PU_CTRL_CR = Register.PU_CTRL, 5
    PU_CTRL_CS = Register.PU_CTRL, 4
    PU_CTRL_PUR = Register.PU_CTRL, 3
    PU_CTRL_PUA = Register.PU_CTRL, 2
    PU_CTRL_PUD = Register.PU_CTRL, 1
    PU_CTRL_RR = Register.PU_CTRL, 0

    CTRL1_CRP = Register.CTRL1, 7
    CTRL1_UNIMPLEMENTED = Register.CTRL1, 6
    CTRL1_VLDO2 = Register.CTRL1, 5
    CTRL1_VLDO1 = Register.CTRL1, 4
    CTRL1_VLDO0 = Register.CTRL1, 3
    CTRL1_GAINS2 = Register.CTRL1, 2
    CTRL1_GAINS1 = Register.CTRL1, 1
    CTRL1_GAINS0 = Register.CTRL1, 0

    CTRL2_CHS = Register.CTRL2, 7
    CTRL2_CRS1 = Register.CTRL2, 6
    CTRL2_CRS0 = Register.CTRL2, 5
    CTRL2_UNIMPLEMENTED1 = Register.CTRL2, 4
    CTRL2_UNIMPLEMENTED2 = Register.CTRL2, 3
    CTRL2_CALS = Register.CTRL2, 2
    CTRL2_CALMOD1 = Register.CTRL2, 1
    CTRL2_CALMOD0 = Register.CTRL2, 0

    OCAL1_B2_23 = Register.OCAL1_B2, 7
    OCAL1_B2_22 = Register.OCAL1_B2, 6
    OCAL1_B2_21 = Register.OCAL1_B2, 5
    OCAL1_B2_20 = Register.OCAL1_B2, 4
    OCAL1_B2_19 = Register.OCAL1_B2, 3
    OCAL1_B2_18 = Register.OCAL1_B2, 2
    OCAL1_B2_17 = Register.OCAL1_B2, 1
    OCAL1_B2_16 = Register.OCAL1_B2, 0

    OCAL1_B1_15 = Register.OCAL1_B1, 7
    OCAL1_B1_14 = Register.OCAL1_B1, 6
    OCAL1_B1_13 = Register.OCAL1_B1, 5
    OCAL1_B1_12 = Register.OCAL1_B1, 4
    OCAL1_B1_11 = Register.OCAL1_B1, 3
    OCAL1_B1_10 = Register.OCAL1_B1, 2
    OCAL1_B1_9 = Register.OCAL1_B1, 1
    OCAL1_B1_8 = Register.OCAL1_B1, 0

    OCAL1_B0_7 = Register.OCAL1_B0, 7
    OCAL1_B0_6 = Register.OCAL1_B0, 6
    OCAL1_B0_5 = Register.OCAL1_B0, 5
    OCAL1_B0_4 = Register.OCAL1_B0, 4
    OCAL1_B0_3 = Register.OCAL1_B0, 3
    OCAL1_B0_2 = Register.OCAL1_B0, 2
    OCAL1_B0_1 = Register.OCAL1_B0, 1
    OCAL1_B0_0 = Register.OCAL1_B0, 0

    GCAL1_B3_31 = Register.GCAL1_B3, 7
    GCAL1_B3_30 = Register.GCAL1_B3, 6
    GCAL1_B3_29 = Register.GCAL1_B3, 5
    GCAL1_B3_28 = Register.GCAL1_B3, 4
    GCAL1_B3_27 = Register.GCAL1_B3, 3
    GCAL1_B3_26 = Register.GCAL1_B3, 2
    GCAL1_B3_25 = Register.GCAL1_B3, 1
    GCAL1_B3_24 = Register.GCAL1_B3, 0

    GCAL1_B2_23 = Register.GCAL1_B2, 7
    GCAL1_B2_22 = Register.GCAL1_B2, 6
    GCAL1_B2_21 = Register.GCAL1_B2, 5
    GCAL1_B2_20 = Register.GCAL1_B2, 4
    GCAL1_B2_19 = Register.GCAL1_B2, 3
    GCAL1_B2_18 = Register.GCAL1_B2, 2
    GCAL1_B2_17 = Register.GCAL1_B2, 1
    GCAL1_B2_16 = Register.GCAL1_B2, 0

    GCAL1_B1_15 = Register.GCAL1_B1, 7
    GCAL1_B1_14 = Register.GCAL1_B1, 6
    GCAL1_B1_13 = Register.GCAL1_B1, 5
    GCAL1_B1_12 = Register.GCAL1_B1, 4
    GCAL1_B1_11 = Register.GCAL1_B1, 3
    GCAL1_B1_10 = Register.GCAL1_B1, 2
    GCAL1_B1_9 = Register.GCAL1_B1, 1
    GCAL1_B1_8 = Register.GCAL1_B1, 0

    GCAL1_B0_7 = Register.GCAL1_B0, 7
    GCAL1_B0_6 = Register.GCAL1_B0, 6
    GCAL1_B0_5 = Register.GCAL1_B0, 5
    GCAL1_B0_4 = Register.GCAL1_B0, 4
    GCAL1_B0_3 = Register.GCAL1_B0, 3
    GCAL1_B0_2 = Register.GCAL1_B0, 2
    GCAL1_B0_1 = Register.GCAL1_B0, 1
    GCAL1_B0_0 = Register.GCAL1_B0, 0

    OCAL2_B2_23 = Register.OCAL2_B2, 7
    OCAL2_B2_22 = Register.OCAL2_B2, 6
    OCAL2_B2_21 = Register.OCAL2_B2, 5
    OCAL2_B2_20 = Register.OCAL2_B2, 4
    OCAL2_B2_19 = Register.OCAL2_B2, 3
    OCAL2_B2_18 = Register.OCAL2_B2, 2
    OCAL2_B2_17 = Register.OCAL2_B2, 1
    OCAL2_B2_16 = Register.OCAL2_B2, 0

    OCAL2_B1_15 = Register.OCAL2_B1, 7
    OCAL2_B1_14 = Register.OCAL2_B1, 6
    OCAL2_B1_13 = Register.OCAL2_B1, 5
    OCAL2_B1_12 = Register.OCAL2_B1, 4
    OCAL2_B1_11 = Register.OCAL2_B1, 3
    OCAL2_B1_10 = Register.OCAL2_B1, 2
    OCAL2_B1_9 = Register.OCAL2_B1, 1
    OCAL2_B1_8 = Register.OCAL2_B1, 0

    OCAL2_B0_7 = Register.OCAL2_B0, 7
    OCAL2_B0_6 = Register.OCAL2_B0, 6
    OCAL2_B0_5 = Register.OCAL2_B0, 5
    OCAL2_B0_4 = Register.OCAL2_B0, 4
    OCAL2_B0_3 = Register.OCAL2_B0, 3
    OCAL2_B0_2 = Register.OCAL2_B0, 2
    OCAL2_B0_1 = Register.OCAL2_B0, 1
    OCAL2_B0_0 = Register.OCAL2_B0, 0

    GCAL2_B3_31 = Register.GCAL2_B3, 7
    GCAL2_B3_30 = Register.GCAL2_B3, 6
    GCAL2_B3_29 = Register.GCAL2_B3, 5
    GCAL2_B3_28 = Register.GCAL2_B3, 4
    GCAL2_B3_27 = Register.GCAL2_B3, 3
    GCAL2_B3_26 = Register.GCAL2_B3, 2
    GCAL2_B3_25 = Register.GCAL2_B3, 1
    GCAL2_B3_24 = Register.GCAL2_B3, 0

    GCAL2_B2_23 = Register.GCAL2_B2, 7
    GCAL2_B2_22 = Register.GCAL2_B2, 6
    GCAL2_B2_21 = Register.GCAL2_B2, 5
    GCAL2_B2_20 = Register.GCAL2_B2, 4
    GCAL2_B2_19 = Register.GCAL2_B2, 3
    GCAL2_B2_18 = Register.GCAL2_B2, 2
    GCAL2_B2_17 = Register.GCAL2_B2, 1
    GCAL2_B2_16 = Register.GCAL2_B2, 0

    GCAL2_B1_15 = Register.GCAL2_B1, 7
    GCAL2_B1_14 = Register.GCAL2_B1, 6
    GCAL2_B1_13 = Register.GCAL2_B1, 5
    GCAL2_B1_12 = Register.GCAL2_B1, 4
    GCAL2_B1_11 = Register.GCAL2_B1, 3
    GCAL2_B1_10 = Register.GCAL2_B1, 2
    GCAL2_B1_9 = Register.GCAL2_B1, 1
    GCAL2_B1_8 = Register.GCAL2_B1, 0

    GCAL2_B0_7 = Register.GCAL2_B0, 7
    GCAL2_B0_6 = Register.GCAL2_B0, 6
    GCAL2_B0_5 = Register.GCAL2_B0, 5
    GCAL2_B0_4 = Register.GCAL2_B0, 4
    GCAL2_B0_3 = Register.GCAL2_B0, 3
    GCAL2_B0_2 = Register.GCAL2_B0, 2
    GCAL2_B0_1 = Register.GCAL2_B0, 1
    GCAL2_B0_0 = Register.GCAL2_B0, 0

    I2C_CTRL_CRSD = Register.I2C_CTRL, 7
    I2C_CTRL_FDR = Register.I2C_CTRL, 6
    I2C_CTRL_SPE = Register.I2C_CTRL, 5
    I2C_CTRL_WPD = Register.I2C_CTRL, 4
    I2C_CTRL_SI = Register.I2C_CTRL, 3
    I2C_CTRL_BOPGA = Register.I2C_CTRL, 2
    I2C_CTRL_TS = Register.I2C_CTRL, 1
    I2C_CTRL_BGPCP = Register.I2C_CTRL, 0

    ADCO_B2_23 = Register.ADCO_B2, 7
    ADCO_B2_22 = Register.ADCO_B2, 6
    ADCO_B2_21 = Register.ADCO_B2, 5
    ADCO_B2_20 = Register.ADCO_B2, 4
    ADCO_B2_19 = Register.ADCO_B2, 3
    ADCO_B2_18 = Register.ADCO_B2, 2
    ADCO_B2_17 = Register.ADCO_B2, 1
    ADCO_B2_16 = Register.ADCO_B2, 0

    ADCO_B1_15 = Register.ADCO_B1, 7
    ADCO_B1_14 = Register.ADCO_B1, 6
    ADCO_B1_13 = Register.ADCO_B1, 5
    ADCO_B1_12 = Register.ADCO_B1, 4
    ADCO_B1_11 = Register.ADCO_B1, 3
    ADCO_B1_10 = Register.ADCO_B1, 2
    ADCO_B1_9 = Register.ADCO_B1, 1
    ADCO_B1_8 = Register.ADCO_B1, 0

    ADCO_B0_7 = Register.ADCO_B0, 7
    ADCO_B0_6 = Register.ADCO_B0, 6
    ADCO_B0_5 = Register.ADCO_B0, 5
    ADCO_B0_4 = Register.ADCO_B0, 4
    ADCO_B0_3 = Register.ADCO_B0, 3
    ADCO_B0_2 = Register.ADCO_B0, 2
    ADCO_B0_1 = Register.ADCO_B0, 1
    ADCO_B0_0 = Register.ADCO_B0, 0

    OTP_B1_15 = Register.OTP_B1, 7
    OTP_B1_14 = Register.OTP_B1, 6
    OTP_B1_13 = Register.OTP_B1, 5
    OTP_B1_12 = Register.OTP_B1, 4
    OTP_B1_11 = Register.OTP_B1, 3
    OTP_B1_10 = Register.OTP_B1, 2
    OTP_B1_9 = Register.OTP_B1, 1
    OTP_B1_8 = Register.OTP_B1, 0

    OTP_B0_7 = Register.OTP_B0, 7
    OTP_B0_6 = Register.OTP_B0, 6
    OTP_B0_5 = Register.OTP_B0, 5
    OTP_B0_4 = Register.OTP_B0, 4
    OTP_B0_3 = Register.OTP_B0, 3
    OTP_B0_2 = Register.OTP_B0, 2
    OTP_B0_1 = Register.OTP_B0, 1
    OTP_B0_0 = Register.OTP_B0, 0


@dataclass
class NAU7802:
    """A Python driver for Nuvoton NAU7802 24-Bit Dual-Channel ADC."""

    DRDY_DIRECTION: ClassVar[str] = 'in'
    """The DRDY GPIO direction."""
    DRDY_INVERTED: ClassVar[bool] = False
    """The DRDY GPIO inverted status."""
    DEVICE_ADDRESS: ClassVar[int] = 0x2A
    """The permanent device address."""
    drdy_gpio: GPIO
    """The DRDY GPIO."""
    i2c: I2C
    """The I2C for the ADC device."""
    timeout: float = 0.01
    """Timeout for sampling."""

    def __post_init__(self) -> None:
        if (self.drdy_gpio.direction != self.DRDY_DIRECTION):
            raise ValueError('invalid GPIO direction')
        elif (self.drdy_gpio.inverted != self.DRDY_INVERTED):
            raise ValueError('invalid GPIO inverted status')

    def read(self, register: Register, data_byte_count: int) -> list[int]:
        """Read register.

        :return: Stored value of register.
        """
        device_address_byte = (self.DEVICE_ADDRESS << 1) | 0
        messages = [I2C.Message([register])]
        self.i2c.transfer(device_address_byte, messages)

        device_address_byte = (self.DEVICE_ADDRESS << 1) | 1
        received_messages = [I2C.Message([0x00]*data_byte_count, read=True)]
        self.i2c.transfer(device_address_byte, received_messages)

        return cast(list[int], received_messages[0].data[0:data_byte_count])

    def write(self, register: Register, data_bytes: list[int]) -> None:
        """Write to register.

        :return: ``None``.
        """
        device_address_byte = (self.DEVICE_ADDRESS << 1) | 0
        messages = [I2C.Message([register, *data_bytes])]
        self.i2c.transfer(device_address_byte, messages)

    def read_bit(self, register: Register, bit: int) -> bool:
        """Read specific bit of a register.

        :return: Value of bit.
        """
        (data_byte,) = self.read(register, 1)

        return bool(data_byte & (1 << bit))

    def write_bit(self, register: Register, bit: int, value: bool) -> None:
        """Write to a specific bit of a register.

        :return: ``None``.
        """
        (data_byte,) = self.read(register, 1)

        if bool(data_byte & (1 << bit)) != value:
            data_byte ^= 1 << bit

            self.write(register, [data_byte])

    def reset(self) -> None:
        """Reset and perform power-on sequencing.

        :return: ``None``.
        """
        self.write_bit(*RegisterBit.PU_CTRL_RR, True)  # type: ignore[call-arg]
        self.write_bit(  # type: ignore[call-arg]
            *RegisterBit.PU_CTRL_RR,
            False,
        )
        self.write_bit(  # type: ignore[call-arg]
            *RegisterBit.PU_CTRL_PUD,
            True,
        )

        while self.read_bit(*RegisterBit.PU_CTRL_PUR) != 1:
            sleep(self.timeout)

        self.write_bit(*RegisterBit.PU_CTRL_CS, True)  # type: ignore[call-arg]

    def select_channel(self, channel: int) -> None:
        """Select input channel.

        :return: ``None``.
        """
        assert (channel == 1 or channel == 2), "invalid input channel"

        if channel == 1:
            self.write_bit(  # type: ignore[call-arg]
                *RegisterBit.CTRL2_CHS,
                False,
            )
        elif channel == 2:
            self.write_bit(  # type: ignore[call-arg]
                *RegisterBit.CTRL2_CHS,
                True,
            )

    def sample(self) -> int:
        """Return ADC conversion result when conversion is complete and
        new data are available for readout.

        :return: Conversion result.
        """
        while not self.drdy_gpio.read():
            sleep(self.timeout)

        adc_value = self.read(Register.ADCO_B2, 3)

        return adc_value[0] << 16 | adc_value[1] << 8 | adc_value[0]

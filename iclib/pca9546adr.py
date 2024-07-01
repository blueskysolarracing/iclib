"""This module implements the PCA9546ADR driver."""

from periphery import I2C


class PCA9546A:
    """
    A python driver for Texas Instruments PCA9546ADR,
    Low Voltage 4-Channel I2C and SMBus Switch with Reset Function
    """

    def __init__(self, address):
        """
        Initialize PCA9546A I2C switch.

        :param address: I2C address of PCA9546A.
        """

        self.address = address
        self.i2c = I2C("/dev/i2c-0")  # Need bus number

    def channel_select(self, channels):
        """
        Select channel(s) to enable.

        :param channels: A list of integers (0-3) corresponding
        to channels to enable.
        """

        if not all(0 <= ch <= 3 for ch in channels):
            raise ValueError("Channel numbers must be between 0 and 3.")

        write_value = 0x00
        for ch in channels:
            write_value = write_value | (1 << ch)

        self.i2c.transfer(self.address, [I2C.Message([write_value])])

    def channel_read(self):
        """
        Read currently selected channel(s).

        :return: Byte indicating selected channel(s).
        """

        read = I2C.Message([0x00], read=True)
        self.i2c.transfer(self.address, [read])
        return read.data

    def reset(self):
        """
        Reset PCA9546A by disabling all channels.
        """

        self.i2c.transfer(self.address, [I2C.Message([0x0])])

    def close(self):
        """
        Close I2C bus.
        """

        self.i2c.close()

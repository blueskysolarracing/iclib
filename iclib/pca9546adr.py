"""This module implements the PCA9546ADR driver."""

from periphery import I2C


class PCA9546A:
    """A python driver for Texas Instruments PCA9546ADR, Low Voltage
    4-Channel I2C and SMBus Switch with Reset Function.
    """

    def __init__(self, address: int, i2c: I2C) -> None:
        """Initialize PCA9546A I2C switch.

        :param address: I2C address of PCA9546A.
        """
        self.address = address
        self.i2c = i2c

    def channel_select(self, channels: list[int]) -> None:
        """Select channel(s) to enable.

        :param channels: A list of integers (0-3) corresponding
        to channels to enable.
        """
        if not all(0 <= ch <= 3 for ch in channels):
            raise ValueError("Channel numbers must be between 0 and 3.")

        write_value = 0x00

        for ch in channels:
            write_value = write_value | (1 << ch)

        self.i2c.transfer(self.address, [I2C.Message([write_value])])

    def channel_read(self) -> int:
        """Read currently selected channel(s).

        :return: Byte indicating selected channel(s).
        """
        read = I2C.Message([0x00], read=True)

        self.i2c.transfer(self.address, [read])

        return read.data[0]

    def reset(self) -> None:
        """Reset PCA9546A by disabling all channels."""
        self.i2c.transfer(self.address, [I2C.Message([0x0])])

    def close(self) -> None:
        """Close I2C bus."""
        self.i2c.close()

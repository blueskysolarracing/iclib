from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

from periphery import GPIO


@dataclass
class SN74HCS137:
    """A Python driver for Texas instruments SN74HCS137 3- to 8-Line
    Decoder/Demultiplexer with Address Latches and SchmittTrigger Inputs
    """

    class Address(IntEnum):
        """The enum class for addresses."""

        Y0: int = 0b000
        """Output 0."""
        Y1: int = 0b001
        """Output 1."""
        Y2: int = 0b010
        """Output 2."""
        Y3: int = 0b011
        """Output 3."""
        Y4: int = 0b100
        """Output 4."""
        Y5: int = 0b101
        """Output 5."""
        Y6: int = 0b110
        """Output 6."""
        Y7: int = 0b111
        """Output 7."""

    LATCH_ENABLE_GPIO_DIRECTION: ClassVar[str] = 'out'
    """The latch enable GPIO direction."""
    STROBE_INPUT_0_GPIO_DIRECTION: ClassVar[str] = 'out'
    """The strobe input 0 GPIO direction."""
    STROBE_INPUT_1_GPIO_DIRECTION: ClassVar[str] = 'out'
    """The strobe input 1 GPIO direction."""
    ADDRESS_SELECT_0_GPIO_DIRECTION: ClassVar[str] = 'out'
    """The address select 0 GPIO direction."""
    ADDRESS_SELECT_1_GPIO_DIRECTION: ClassVar[str] = 'out'
    """The address select 1 GPIO direction."""
    ADDRESS_SELECT_2_GPIO_DIRECTION: ClassVar[str] = 'out'
    """The address select 2 GPIO direction."""
    LATCH_ENABLE_GPIO_INVERTED: ClassVar[bool] = True
    """The latch enable GPIO inverted status."""
    STROBE_INPUT_0_GPIO_INVERTED: ClassVar[bool] = False
    """The strobe input 0 GPIO inverted status."""
    STROBE_INPUT_1_GPIO_INVERTED: ClassVar[bool] = True
    """The strobe input 1 GPIO inverted status."""
    ADDRESS_SELECT_0_GPIO_INVERTED: ClassVar[bool] = False
    """The address select 0 GPIO inverted status."""
    ADDRESS_SELECT_1_GPIO_INVERTED: ClassVar[bool] = False
    """The address select 1 GPIO inverted status."""
    ADDRESS_SELECT_2_GPIO_INVERTED: ClassVar[bool] = False
    """The address select 2 GPIO inverted status."""
    latch_enable_gpio: GPIO
    """The latch enable GPIO."""
    strobe_input_0_gpio: GPIO
    """The strobe input 0 GPIO."""
    strobe_input_1_gpio: GPIO
    """The strobe input 1 GPIO."""
    address_select_0_gpio: GPIO
    """The address select 0 GPIO."""
    address_select_1_gpio: GPIO
    """The address select 1 GPIO."""
    address_select_2_gpio: GPIO
    """The address select 2 GPIO."""

    def __post_init__(self) -> None:
        if (
                (
                    self.latch_enable_gpio.direction
                    != self.LATCH_ENABLE_GPIO_DIRECTION
                )
                or (
                    self.strobe_input_0_gpio.direction
                    != self.STROBE_INPUT_0_GPIO_DIRECTION
                )
                or (
                    self.strobe_input_1_gpio.direction
                    != self.STROBE_INPUT_1_GPIO_DIRECTION
                )
                or (
                    self.address_select_0_gpio.direction
                    != self.ADDRESS_SELECT_0_GPIO_DIRECTION
                )
                or (
                    self.address_select_1_gpio.direction
                    != self.ADDRESS_SELECT_1_GPIO_DIRECTION
                )
                or (
                    self.address_select_2_gpio.direction
                    != self.ADDRESS_SELECT_2_GPIO_DIRECTION
                )
        ):
            raise ValueError('invalid GPIO direction')
        elif (
                (
                    self.latch_enable_gpio.direction
                    != self.LATCH_ENABLE_GPIO_INVERTED
                )
                or (
                    self.strobe_input_0_gpio.direction
                    != self.STROBE_INPUT_0_GPIO_INVERTED
                )
                or (
                    self.strobe_input_1_gpio.direction
                    != self.STROBE_INPUT_1_GPIO_INVERTED
                )
                or (
                    self.address_select_0_gpio.direction
                    != self.ADDRESS_SELECT_0_GPIO_INVERTED
                )
                or (
                    self.address_select_1_gpio.direction
                    != self.ADDRESS_SELECT_1_GPIO_INVERTED
                )
                or (
                    self.address_select_2_gpio.direction
                    != self.ADDRESS_SELECT_2_GPIO_INVERTED
                )
        ):
            raise ValueError('invalid GPIO inverted status')

    def enable_latch(self) -> None:
        """Enable the latch.

        :return: ``None``.
        """
        self.latch_enable_gpio.write(True)

    def disable_latch(self) -> None:
        """Disable the latch.

        :return: ``None``.
        """
        self.latch_enable_gpio.write(False)

    def select(self, address: Address) -> None:
        """Select the address.

        :param: The selected address.
        :return: ``None``.
        """
        self.disable_latch()
        self.strobe_input_0_gpio.write(True)
        self.strobe_input_1_gpio.write(True)
        self.address_select_0_gpio.write(bool(address & (1 << 0)))
        self.address_select_1_gpio.write(bool(address & (1 << 1)))
        self.address_select_2_gpio.write(bool(address & (1 << 2)))
        self.enable_latch()

    def deselect(self) -> None:
        """Deselect.

        :return: ``None``.
        """
        self.strobe_input_0_gpio.write(False)
        self.strobe_input_1_gpio.write(False)

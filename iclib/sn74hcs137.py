"""This module implements the SN74HCS137 driver."""

from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

from periphery import GPIO


class Address(IntEnum):
    """The enum class for addresses."""

    Y0 = 0b000
    """Output 0."""
    Y1 = 0b001
    """Output 1."""
    Y2 = 0b010
    """Output 2."""
    Y3 = 0b011
    """Output 3."""
    Y4 = 0b100
    """Output 4."""
    Y5 = 0b101
    """Output 5."""
    Y6 = 0b110
    """Output 6."""
    Y7 = 0b111
    """Output 7."""

    @property
    def A2(self) -> bool:
        """Get ``A2`` of the input channel.

        :return: ``A2``.
        """
        return bool(self & 0b100)

    @property
    def A1(self) -> bool:
        """Get ``A1`` of the input channel.

        :return: ``A1``.
        """
        return bool(self & 0b010)

    @property
    def A0(self) -> bool:
        """Get ``A0`` of the input channel.

        :return: ``A0``.
        """
        return bool(self & 0b001)


@dataclass
class SN74HCS137:
    """A Python driver for Texas instruments SN74HCS137 3- to 8-Line
    Decoder/Demultiplexer with Address Latches and SchmittTrigger Inputs
    """

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
                    self.latch_enable_gpio.inverted
                    != self.LATCH_ENABLE_GPIO_INVERTED
                )
                or (
                    self.strobe_input_0_gpio.inverted
                    != self.STROBE_INPUT_0_GPIO_INVERTED
                )
                or (
                    self.strobe_input_1_gpio.inverted
                    != self.STROBE_INPUT_1_GPIO_INVERTED
                )
                or (
                    self.address_select_0_gpio.inverted
                    != self.ADDRESS_SELECT_0_GPIO_INVERTED
                )
                or (
                    self.address_select_1_gpio.inverted
                    != self.ADDRESS_SELECT_1_GPIO_INVERTED
                )
                or (
                    self.address_select_2_gpio.inverted
                    != self.ADDRESS_SELECT_2_GPIO_INVERTED
                )
        ):
            raise ValueError('invalid GPIO inverted status')

    def enable_latch(self) -> None:
        """Enable the latch.

        The previous state is retained.

        :return: ``None``.
        """
        self.latch_enable_gpio.write(False)

    def disable_latch(self) -> None:
        """Disable the latch.

        :return: ``None``.
        """
        self.latch_enable_gpio.write(True)

    def select(self, address: Address) -> None:
        """Select the address.

        :param: The selected address.
        :return: ``None``.
        """
        self.strobe_input_0_gpio.write(True)
        self.strobe_input_1_gpio.write(True)
        self.address_select_0_gpio.write(address.A0)
        self.address_select_1_gpio.write(address.A1)
        self.address_select_2_gpio.write(address.A2)

    def deselect(self) -> None:
        """Deselect.

        :return: ``None``.
        """
        self.strobe_input_0_gpio.write(False)
        self.strobe_input_1_gpio.write(False)

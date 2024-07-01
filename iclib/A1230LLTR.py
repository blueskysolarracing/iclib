"""This module implements the A1230LLTR-T driver."""

from dataclasses import dataclass
from typing import ClassVar

from periphery import GPIO


@dataclass
class A1230LLTR:
    """A Python driver for Allegro MicroSystems A1230LLTR-T Hall effect sensor 
    with quadrature output
    """

    OUTPUT_A_DIRECTION: ClassVar[str] = 'in'
    """The output A GPIO direction."""
    OUTPUT_B_DIRECTION: ClassVar[str] = 'in'
    """The output B GPIO direction."""
    OUTPUT_A_INVERTED: ClassVar[bool] = False
    """The output A GPIO inverted status."""
    OUTPUT_B_INVERTED: ClassVar[bool] = False
    """The output B GPIO inverted status."""
    output_A_gpio: GPIO 
    """The output A GPIO."""
    output_B_gpio: GPIO 
    """The output B GPIO."""

    def __post_init__(self) -> None:
        if (
                (
                    self.output_A_gpio.direction
                    != self.OUTPUT_A_DIRECTION
                )
                or (
                    self.output_B_gpio.direction
                    != self.OUTPUT_B_DIRECTION
                )
        ):
            raise ValueError('invalid GPIO direction')
        elif (
                (
                    self.output_A_gpio.inverted
                    != self.OUTPUT_A_INVERTED
                )
                or (
                    self.output_B_gpio.inverted
                    != self.OUTPUT_B_INVERTED
                )
        ):
            raise ValueError('invalid GPIO inverted status')
        
    def read_a(self) -> bool:
        """Read OUTPUTA pin.

        :return: Pin value for output A (E1).
        """
        return self.output_A_gpio.read()
    
    def read_b(self) -> bool:
        """Read OUTPUTB pin.

        :return: Pin value for output B (E2).
        """
        return self.output_B_gpio.read()
        
    
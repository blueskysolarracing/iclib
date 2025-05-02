"""This module implements the A1230 driver."""

from dataclasses import dataclass, field
from typing import ClassVar

from periphery import GPIO

from iclib.utilities import FrequencyMonitor


@dataclass
class A1230:
    """A Python driver for Allegro MicroSystems A1230 Hall effect sensor
    with quadrature output
    """

    OUTPUTA_DIRECTION: ClassVar[str] = 'in'
    """The OUTPUTA GPIO direction."""
    OUTPUTB_DIRECTION: ClassVar[str] = 'in'
    """The OUTPUTB GPIO direction."""
    OUTPUTA_INVERTED: ClassVar[bool] = False
    """The OUTPUTA GPIO inverted status."""
    OUTPUTB_INVERTED: ClassVar[bool] = False
    """The OUTPUTB GPIO inverted status."""
    outputa_gpio: GPIO
    """The OUTPUTA GPIO."""
    outputb_gpio: GPIO
    """The OUTPUTB GPIO."""
    frequency_monitor_sample_count: int = field(default=5)
    """The frequency monitor sample count."""
    frequency_monitor_poll_timeout: float = field(default=1)
    """The frequency monitor poll timeout."""
    outputa_frequency_monitor: FrequencyMonitor = field(init=False)
    """The OUTPUTA frequency monitor."""
    outputb_frequency_monitor: FrequencyMonitor = field(init=False)
    """The OUTPUTB frequency monitor."""

    def __post_init__(self) -> None:
        if (
                self.outputa_gpio.direction != self.OUTPUTA_DIRECTION
                or self.outputb_gpio.direction != self.OUTPUTB_DIRECTION
        ):
            raise ValueError('invalid GPIO direction')
        elif (
                self.outputa_gpio.inverted != self.OUTPUTA_INVERTED
                or self.outputb_gpio.inverted != self.OUTPUTB_INVERTED
        ):
            raise ValueError('invalid GPIO inverted status')

        self.outputa_frequency_monitor = FrequencyMonitor(
            self.outputa_gpio,
            self.frequency_monitor_sample_count,
            self.frequency_monitor_poll_timeout,
        )
        self.outputb_frequency_monitor = FrequencyMonitor(
            self.outputb_gpio,
            self.frequency_monitor_sample_count,
            self.frequency_monitor_poll_timeout,
        )

    @property
    def OUTPUTA(self) -> bool:
        """Read OUTPUTA pin.

        :return: Pin value for OUTPUTA (E1).
        """
        return self.outputa_gpio.read()

    @property
    def OUTPUTB(self) -> bool:
        """Read OUTPUTB pin.

        :return: Pin value for OUTPUTB (E2).
        """
        return self.outputb_gpio.read()

    @property
    def outputa_frequency(self) -> float:
        """Get the OUTPUTA frequency.

        :return: The OUTPUTA frequency (in Hz).
        """
        return self.outputa_frequency_monitor.frequency

    @property
    def outputb_frequency(self) -> float:
        """Get the OUTPUTB frequency.

        :return: The OUTPUTB frequency (in Hz).
        """
        return self.outputb_frequency_monitor.frequency

    def stop(self) -> None:
        self.outputa_frequency_monitor.stop()
        self.outputb_frequency_monitor.stop()

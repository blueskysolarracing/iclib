"""This module implements various utilities."""

from collections.abc import Callable
from collections import deque
from dataclasses import dataclass, field
from threading import Event, Lock, Thread
from time import time
from typing import Any, ClassVar
from enum import IntEnum

from periphery import GPIO, I2C, SPI


def bit_getter(index: int) -> Callable[[int], bool]:
    """Return a callable that gets a bit at an index.

    >>> zero = bit_getter(0)
    >>> one = bit_getter(1)
    >>> two = bit_getter(2)
    >>> three = bit_getter(3)
    >>> zero(0b1010)
    False
    >>> one(0b1010)
    True
    >>> two(0b1010)
    False
    >>> three(0b1010)
    True

    :param index: The bit index.
    :return: The bit getter.
    """
    return lambda value: bool(value & (1 << index))


def twos_complement(value: int, bit_count: int) -> int:
    """If a value represents a negative number, perform two's complement
    on it.

    >>> bin(twos_complement(0b0101, 4))
    '0b101'
    >>> bin(twos_complement(0b1101, 4))
    '-0b11'
    >>> bin(twos_complement(0b00001011, 8))
    '0b1011'
    >>> bin(twos_complement(0b10001011, 8))
    '-0b1110101'

    :param value: The value.
    :param bit_count: The number of bits in the value.
    :return: The negated value.
    """
    sign_bit = (1 << (bit_count - 1))
    value = (value & (sign_bit - 1)) - (value & sign_bit)

    return value


def lsb_bits_to_byte(*bits: bool) -> int:
    """Convert LSB bits to a byte.

    >>> bin(lsb_bits_to_byte(True, True, False, False, True))
    '0b10011'

    :param bits: The LSB bits.
    :return: The byte.
    """
    byte = 0

    for i, bit in enumerate(bits):
        byte |= bit << i

    return byte


def msb_bits_to_byte(*bits: bool) -> int:
    """Convert MSB bits to a byte.

    >>> bin(msb_bits_to_byte(True, True, False, False, True))
    '0b11001'

    :param bits: The MSB bits.
    :return: The byte.
    """
    byte = 0

    for bit in bits:
        byte <<= 1
        byte |= bit

    return byte


@dataclass
class FrequencyMonitor:
    """Calculate the frequency of how frequently a GPIO is triggered.

    The GPIO can be configured to be triggered on any or both edges.
    """

    GPIO_EDGE: ClassVar[str] = 'both'
    """The GPIO edge status."""
    gpio: GPIO
    """The GPIO to be monitored."""
    sample_count: int = field(default=5)
    """The number of samples in the sliding window."""
    poll_timeout: float = field(default=1)
    """The poll timeout."""
    _lock: Lock = field(init=False, default_factory=Lock)
    _frequency: float = field(init=False, default=0)
    _stoppage: Event = field(init=False, default_factory=Event)
    _thread: Thread = field(init=False)

    def __post_init__(self) -> None:
        if self.gpio.edge != self.GPIO_EDGE:
            raise ValueError('invalid GPIO edge')

        self._thread = Thread(target=self._monitor, daemon=True)

        self._thread.start()

    def _monitor(self) -> None:
        timestamps = deque[float](maxlen=self.sample_count)

        while not self._stoppage.is_set():
            if self.gpio.poll(self.poll_timeout):
                self.gpio.read_event()
                timestamps.append(time())

                if len(timestamps) > 1:
                    time_difference = timestamps[-1] - timestamps[0]

                    if time_difference:
                        self.frequency = (
                            (len(timestamps) - 1)
                            / 2
                            / time_difference
                        )

    @property
    def frequency(self) -> float:
        """Get the frequency.

        :return: The frequency (in hertz).
        """
        with self._lock:
            return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        """Set the frequency.

        :param value: The new frequency value.
        :return: ``None``.
        """
        with self._lock:
            self._frequency = value

    def stop(self) -> None:
        """Stop the frequency monitor.

        :return: ``None``.
        """
        self._stoppage.set()
        self._thread.join()


@dataclass
class ContinuousFrequencyMonitor:
    """Calculate the frequency of an arbitrary analog signal.

    Return the frequency and current reading.
    """

    class Edge(IntEnum):
        RISING = 0x01
        FALLING = 0x02
        BOTH = 0x03

    threshold: float
    value_getter: Callable[[], float]
    window: float | None = field(default=1)
    edge: Edge = field(default=Edge.BOTH)
    sample_count: int = field(default=5)

    _lock1: Lock = field(init=False, default_factory=Lock)
    _lock2: Lock = field(init=False, default_factory=Lock)
    _frequency: float = field(init=False, default=0)
    _reading: float = field(init=False, default=0)
    _stoppage: Event = field(init=False, default_factory=Event)
    _thread: Thread = field(init=False)

    def __post_init__(self) -> None:
        self._thread = Thread(target=self._monitor, daemon=True)

        self._thread.start()

    def _monitor(self) -> None:
        timestamps = deque[float](maxlen=self.sample_count)
        previous_value = 0.0
        previous_time = time()

        while not self._stoppage.is_set():
            current_value = self.value_getter()
            current_time = time()
            rising = previous_value < self.threshold < current_value
            falling = previous_value > self.threshold > current_value

            self.reading = current_value

            if self.edge == self.Edge.RISING:
                crossed = rising
            elif self.edge == self.Edge.FALLING:
                crossed = falling
            else:
                crossed = rising or falling

            if self.window is not None:
                while (
                    len(timestamps) > 0
                    and (current_time - timestamps[0]) > self.window
                ):
                    timestamps.popleft()

            if crossed:
                timestamps.append((current_time + previous_time) / 2)

            if len(timestamps) > 1:
                time_difference = timestamps[-1] - timestamps[0]
                if self.edge == self.Edge.BOTH:
                    self.frequency = (
                        (len(timestamps) - 1) / 2 / time_difference
                    )
                else:
                    self.frequency = (
                        (len(timestamps) - 1) / time_difference
                    )
            else:
                self.frequency = 0.0

            previous_value = current_value
            previous_time = current_time

    @property
    def frequency(self) -> float:
        """Get the frequency.

        :return: The frequency (in hertz).
        """
        with self._lock1:
            return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        """Set the frequency.

        :param value: The new frequency value.
        :return: ``None``.
        """
        with self._lock1:
            self._frequency = value

    @property
    def reading(self) -> float:
        """Get the reading.

        :return: The reading.
        """
        with self._lock2:
            return self._reading

    @reading.setter
    def reading(self, value: float) -> None:
        """Set the reading.

        :param value: The new reading value.
        :return: ``None``.
        """
        with self._lock2:
            self._reading = value

    def stop(self) -> None:
        """Stop the frequency monitor.

        :return: ``None``.
        """
        self._stoppage.set()
        self._thread.join()


@dataclass
class ManualCSSPI:
    """SPI interface with manually driven GPIO as chip-select.

    The manually driven chip-select must be active-low.
    """

    CHIP_SELECT_GPIO_INVERTED: ClassVar[bool] = True
    """The chip-select inverted status (active-low)."""
    chip_select_gpio: GPIO
    """The chip-select GPIO."""
    spi: SPI
    """The SPI interface."""

    def __post_init__(self) -> None:
        if self.chip_select_gpio.inverted != self.CHIP_SELECT_GPIO_INVERTED:
            raise ValueError('chip select gpio should be inverted')

        self.chip_select_gpio.write(False)

    def transfer(
            self,
            data: bytes | bytearray | list[int],
    ) -> bytes | bytearray | list[int]:
        """Transmit and receive data from SPI.

        :param data: The transmitted data.
        :return: The received data.
        """
        self.chip_select_gpio.write(True)

        received_data = self.spi.transfer(data)

        self.chip_select_gpio.write(False)

        return received_data

    def __getattr__(self, name: str) -> Any:
        return getattr(self.spi, name)


@dataclass
class LockedSPI:
    """SPI interface with mutually exclusive access."""

    spi: SPI
    """The SPI interface."""
    _lock: Lock = field(default_factory=Lock)

    def transfer(
            self,
            data: bytes | bytearray | list[int],
    ) -> bytes | bytearray | list[int]:
        """Transmit and receive data from SPI with mutually exclusive
        access.

        :param data: The transmitted data.
        :return: The received data.
        """
        with self._lock:
            received_data = self.spi.transfer(data)

        return received_data

    def __getattr__(self, name: str) -> Any:
        return getattr(self.spi, name)


@dataclass
class LockedI2C:
    """I2C interface with mutually exclusive access."""

    i2c: I2C
    """The I2C interface."""
    _lock: Lock = field(default_factory=Lock)

    def transfer(self, address: int, messages: list[I2C.Message]) -> None:
        """Transmit and receive data from I2C with mutually exclusive
        access.

        :param messages: List of I2C.Message messages.
        :return: None.
        """
        with self._lock:
            self.i2c.transfer(address, messages)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.spi, name)

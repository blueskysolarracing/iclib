from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum
from threading import Event, Thread
from time import sleep
from typing import Any, ClassVar

from periphery import GPIO


@dataclass
class RotaryEncoder:
    class Direction(IntEnum):
        Clockwise: int = 1
        Counterclockwise: int = -1

    GPIO_DIRECTION: ClassVar[str] = 'in'
    a_gpio: GPIO
    b_gpio: GPIO
    callback: Callable[[Direction], Any]
    timeout: float = field(default=0.01)
    _stoppage: Event = field(init=False, default_factory=Event)
    _thread: Thread = field(init=False)

    def __post_init__(self) -> None:
        if (
                self.a_gpio.direction != self.GPIO_DIRECTION
                or self.b_gpio.direction != self.GPIO_DIRECTION
        ):
            raise ValueError('the pins must be input pins')

        self._thread = Thread(target=self._monitor, daemon=True)

        self._thread.run()

    @property
    def state(self) -> tuple[bool, bool]:
        return self.a_gpio.read(), self.b_gpio.read()

    def _monitor(self) -> None:
        previous_state = self.state

        while not self._stoppage.is_set():
            state = self.state

            match previous_state, state:
                case (True, True), (False, True):
                    self.callback(self.Direction.Clockwise)
                case (True, True), (True, False):
                    self.callback(self.Direction.Counterclockwise)

            previous_state = state

            sleep(self.timeout)

    def stop(self) -> None:
        self._stoppage.set()
        self._thread.join()

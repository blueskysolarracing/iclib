from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum
from threading import Event, Thread
from typing import Any, ClassVar

from periphery import GPIO


@dataclass
class RotaryEncoder:
    class Direction(IntEnum):
        Clockwise = 1
        Counterclockwise = -1

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

        self._thread.start()

    @property
    def state(self) -> tuple[bool, bool]:
        return self.a_gpio.read(), self.b_gpio.read()

    def _monitor(self) -> None:
        previous_state = self.state

        while not self._stoppage.wait(self.timeout):
            state = self.state

            # print(state)

            direction: RotaryEncoder.Direction | None

            match previous_state, state:
                case (True, True), (False, True):
                    direction = self.Direction.Clockwise
                case (True, True), (True, False):
                    direction = self.Direction.Counterclockwise
                case _:
                    direction = None

            if direction is not None:
                self.callback(direction)

            previous_state = state

    def stop(self) -> None:
        self._stoppage.set()
        self._thread.join()

from struct import calcsize
from unittest import TestCase, main

from iclib.wavesculptor22 import WaveSculptor22


class WaveSculptor22TestCase(TestCase):
    def test_motor_control_broadcast_message_format_sizes(self) -> None:
        for type_ in WaveSculptor22.MOTOR_CONTROL_BROADCAST_MESSAGE_TYPES:
            self.assertEqual(calcsize(type_.format_), 8)


if __name__ == '__main__':
    main()  # pragma: no cover

from struct import calcsize
from unittest import TestCase, main
from unittest.mock import MagicMock

from iclib.wavesculptor22 import WaveSculptor22


class WaveSculptor22TestCase(TestCase):
    def test_motor_control_broadcast_message_format_sizes(self) -> None:
        for type_ in WaveSculptor22.MOTOR_CONTROL_BROADCAST_MESSAGE_TYPES:
            self.assertEqual(calcsize(type_.FORMAT), 8)

    def test_motor_drive(self) -> None:
        mock_can_bus = MagicMock()
        wavesculptor22 = WaveSculptor22(mock_can_bus, 0x500, 0x400)

        wavesculptor22.motor_drive_torque_control_mode(0.2)

        message = mock_can_bus.send.call_args.args[0]

        self.assertEqual(message.arbitration_id, 0x501)
        self.assertEqual(
            message.data,
            bytes([0x00, 0x40, 0x9C, 0x46, 0xCD, 0xCC, 0x4C, 0x3E]),
        )

        wavesculptor22.motor_drive_torque_control_mode(0.5)

        message = mock_can_bus.send.call_args.args[0]

        self.assertEqual(message.arbitration_id, 0x501)
        self.assertEqual(
            message.data,
            bytes([0x00, 0x40, 0x9C, 0x46, 0x00, 0x00, 0x00, 0x3F]),
        )

    def test_motor_power(self) -> None:
        mock_can_bus = MagicMock()
        wavesculptor22 = WaveSculptor22(mock_can_bus, 0x500, 0x400)

        wavesculptor22.motor_power(1)

        message = mock_can_bus.send.call_args.args[0]

        self.assertEqual(message.arbitration_id, 0x502)
        self.assertEqual(
            message.data,
            bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x3F]),
        )

    def test_motor_reset(self) -> None:
        mock_can_bus = MagicMock()
        wavesculptor22 = WaveSculptor22(mock_can_bus, 0x500, 0x400)

        wavesculptor22.reset()

        message = mock_can_bus.send.call_args.args[0]

        self.assertEqual(message.arbitration_id, 0x503)
        self.assertEqual(message.data, bytes([0x00] * 8))

    def test_active_motor_change(self) -> None:
        mock_can_bus = MagicMock()
        wavesculptor22 = WaveSculptor22(mock_can_bus, 0x500, 0x400)

        wavesculptor22.active_motor_change(5)

        message = mock_can_bus.send.call_args.args[0]

        self.assertEqual(message.arbitration_id, 0x412)
        self.assertEqual(
            message.data,
            bytes([0x00, 0x05, 0x54, 0x4F, 0x4D, 0x54, 0x43, 0x41][::-1]),
        )


if __name__ == '__main__':
    main()  # pragma: no cover

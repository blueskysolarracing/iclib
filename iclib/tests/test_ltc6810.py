from itertools import chain
from unittest import TestCase, main
from unittest.mock import MagicMock

from iclib.ltc6810 import LTC6810


class LTC6810TestCase(TestCase):
    def test_get_voltage(self) -> None:
        self.assertAlmostEqual(LTC6810.get_voltage([0xE8, 0x80]), 3.3)

    def test_get_packet_error_code_bytes(self) -> None:
        self.assertEqual(
            LTC6810.get_packet_error_code_bytes([0x00, 0x01]),
            (0b00111101, 0b01101110),
        )

    def test_start_cell_voltage_adc_conversion_and_poll_status(self) -> None:
        mock_spi = MagicMock(
            mode=LTC6810.SPI_MODE,
            max_speed=LTC6810.MIN_SPI_MAX_SPEED,
            bit_order=LTC6810.SPI_BIT_ORDER,
            bits_per_word=LTC6810.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        ltc6810 = LTC6810(mock_spi)

        ltc6810.ADCV(LTC6810.CHMode.M7000, False, 0, 0, sleep=False)

        command_bytes = 0b10000011, 0b01100000
        packet_error_code_bytes = LTC6810.get_packet_error_code_bytes(
            command_bytes,
        )
        transmitted_bytes = list(command_bytes + packet_error_code_bytes)

        mock_spi.transfer.assert_called_once_with(transmitted_bytes)

    def test_read_cell_voltage_register_group_a(self) -> None:
        mock_spi = MagicMock(
            mode=LTC6810.SPI_MODE,
            max_speed=LTC6810.MIN_SPI_MAX_SPEED,
            bit_order=LTC6810.SPI_BIT_ORDER,
            bits_per_word=LTC6810.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0] * 6
        ltc6810 = LTC6810(mock_spi)

        group = ltc6810.RDCVA(0)

        self.assertAlmostEqual(group.C1V, 0)
        self.assertAlmostEqual(group.C2V, 0)
        self.assertAlmostEqual(group.C3V, 0)

        command_bytes = 0b10000000, 0b00000100
        data_bytes = [0xFF] * 6
        transmitted_bytes = list(
            chain(
                command_bytes,
                LTC6810.get_packet_error_code_bytes(command_bytes),
                data_bytes,
                LTC6810.get_packet_error_code_bytes(data_bytes),
            ),
        )

        mock_spi.transfer.assert_called_once_with(transmitted_bytes)

    def test_read_cell_voltage_register_group_b(self) -> None:
        mock_spi = MagicMock(
            mode=LTC6810.SPI_MODE,
            max_speed=LTC6810.MIN_SPI_MAX_SPEED,
            bit_order=LTC6810.SPI_BIT_ORDER,
            bits_per_word=LTC6810.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0] * 6
        ltc6810 = LTC6810(mock_spi)

        group = ltc6810.RDCVB(0)

        self.assertAlmostEqual(group.C4V, 0)
        self.assertAlmostEqual(group.C5V, 0)
        self.assertAlmostEqual(group.C6V, 0)

        command_bytes = 0b10000000, 0b00000110
        data_bytes = [0xFF] * 6
        transmitted_bytes = list(
            chain(
                command_bytes,
                LTC6810.get_packet_error_code_bytes(command_bytes),
                data_bytes,
                LTC6810.get_packet_error_code_bytes(data_bytes),
            ),
        )

        mock_spi.transfer.assert_called_once_with(transmitted_bytes)


if __name__ == '__main__':
    main()  # pragma: no cover

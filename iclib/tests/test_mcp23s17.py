from unittest import TestCase, main
from unittest.mock import call, MagicMock

from iclib.mcp23s17 import MCP23S17, Mode, Port, Register


class MCP23S17TestCase(TestCase):
    def test_read_register(self) -> None:
        mock_hardware_reset_gpio = MagicMock()
        mock_interrupt_output_a_gpio = MagicMock()
        mock_interrupt_output_b_gpio = MagicMock()
        mock_hardware_reset_gpio.read.return_value = False
        mock_interrupt_output_a_gpio.read.return_value = False
        mock_interrupt_output_b_gpio.read.return_value = False
        mock_spi = MagicMock(
            mode=MCP23S17.SPI_MODES[0],
            max_speed=MCP23S17.MAX_SPI_MAX_SPEED,
            bit_order=MCP23S17.SPI_BIT_ORDER,
            bits_per_word=MCP23S17.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111, 0b11111111, 0b00000000]
        mcp23s17 = MCP23S17(
            mock_hardware_reset_gpio,
            mock_interrupt_output_a_gpio,
            mock_interrupt_output_b_gpio,
            mock_spi,
        )

        self.assertEqual(
            mcp23s17.read_register(Port.PORTA, Register.INTCON),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000001, 0x08, 0xFF])
        mock_spi.clear_calls()
        mock_spi.reset_mock()
        self.assertEqual(
            mcp23s17.read_register(Port.PORTB, Register.INTCON),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000001, 0x09, 0xFF])
        mock_spi.reset_mock()

        mcp23s17.mode = Mode.EIGHT_BIT_MODE

        mock_spi.transfer.assert_has_calls(
            [
                call([0b01000001, 0x0A, 0xFF]),
                call([0b01000000, 0x0A, 0b10000000]),
            ],
        )
        mock_spi.reset_mock()

        self.assertEqual(
            mcp23s17.read_register(Port.PORTA, Register.INTCON),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000001, 0x04, 0xFF])
        mock_spi.clear_calls()
        mock_spi.reset_mock()
        self.assertEqual(
            mcp23s17.read_register(Port.PORTB, Register.INTCON),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000001, 0x14, 0xFF])

    def test_write_register(self) -> None:
        mock_hardware_reset_gpio = MagicMock()
        mock_interrupt_output_a_gpio = MagicMock()
        mock_interrupt_output_b_gpio = MagicMock()
        mock_hardware_reset_gpio.read.return_value = False
        mock_interrupt_output_a_gpio.read.return_value = False
        mock_interrupt_output_b_gpio.read.return_value = False
        mock_spi = MagicMock(
            mode=MCP23S17.SPI_MODES[0],
            max_speed=MCP23S17.MAX_SPI_MAX_SPEED,
            bit_order=MCP23S17.SPI_BIT_ORDER,
            bits_per_word=MCP23S17.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111, 0b11111111, 0b00000000]
        mcp23s17 = MCP23S17(
            mock_hardware_reset_gpio,
            mock_interrupt_output_a_gpio,
            mock_interrupt_output_b_gpio,
            mock_spi,
        )

        self.assertEqual(
            mcp23s17.write_register(Port.PORTA, Register.INTCON, [0b10101010]),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000000, 0x08, 0xAA])
        mock_spi.clear_calls()
        mock_spi.reset_mock()
        self.assertEqual(
            mcp23s17.write_register(Port.PORTB, Register.INTCON, [0b10101010]),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000000, 0x09, 0xAA])
        mock_spi.reset_mock()

        mcp23s17.mode = Mode.EIGHT_BIT_MODE

        mock_spi.transfer.assert_has_calls(
            [
                call([0b01000001, 0x0A, 0xFF]),
                call([0b01000000, 0x0A, 0b10000000]),
            ],
        )
        mock_spi.reset_mock()

        self.assertEqual(
            mcp23s17.write_register(Port.PORTA, Register.INTCON, [0b10101010]),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000000, 0x04, 0xAA])
        mock_spi.clear_calls()
        mock_spi.reset_mock()
        self.assertEqual(
            mcp23s17.write_register(Port.PORTB, Register.INTCON, [0b10101010]),
            [0b00000000],
        )
        mock_spi.transfer.assert_called_once_with([0b01000000, 0x14, 0xAA])


if __name__ == '__main__':
    main()  # pragma: no cover

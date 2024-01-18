from unittest import TestCase
from unittest.mock import MagicMock

from iclib.mcp4161 import MCP4161


class MCP4161TestCase(TestCase):
    def test_read_data(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[-1],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111, 0b01010101]
        mcp4161 = MCP4161(mock_spi)

        self.assertEqual(mcp4161.read_data(0b1010), 0b101010101)
        mock_spi.transfer.assert_called_once_with([0b10101111, 0b11111111])

    def test_write_data(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[-1],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111, 0b11111111]
        mcp4161 = MCP4161(mock_spi)

        mcp4161.write_data(0b1010, 0b101010101)
        mock_spi.transfer.assert_called_once_with([0b10100001, 0b01010101])

    def test_increment(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[-1],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111]
        mcp4161 = MCP4161(mock_spi)

        mcp4161.increment(MCP4161.MemoryAddress.VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00000100])
        mock_spi.transfer.reset_mock()
        mcp4161.increment(MCP4161.MemoryAddress.NON_VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00100100])

    def test_decrement(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[-1],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111]
        mcp4161 = MCP4161(mock_spi)

        mcp4161.decrement(MCP4161.MemoryAddress.VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00001000])
        mock_spi.transfer.reset_mock()
        mcp4161.decrement(MCP4161.MemoryAddress.NON_VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00101000])

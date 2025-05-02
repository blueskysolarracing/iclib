from unittest import TestCase, main
from unittest.mock import MagicMock

from iclib.mcp4161 import MCP4161, MemoryAddress, STATUSBit, TCONBit


class MCP4161TestCase(TestCase):
    def test_bits(self) -> None:
        for i in range(8):
            tcon_bits = TCONBit(1 << i)
            raw_tcon_bits = (
                tcon_bits.R0B,
                tcon_bits.R0W,
                tcon_bits.R0A,
                tcon_bits.R0HW,
                tcon_bits.R1B,
                tcon_bits.R1W,
                tcon_bits.R1A,
                tcon_bits.R1HW,
            )

            for j, bit in enumerate(raw_tcon_bits):
                if j == i:
                    self.assertTrue(bit)
                else:
                    self.assertFalse(bit)

        for i in range(5):
            status_bits = STATUSBit(1 << i)
            raw_status_bits = (
                status_bits.WP,
                status_bits.SHDN,
                status_bits.WL0,
                status_bits.WL1,
                status_bits.EEWA,
            )

            for j, bit in enumerate(raw_status_bits):
                if j == i:
                    self.assertTrue(bit)
                else:
                    self.assertFalse(bit)

    def test_read(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[0],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111, 0b01010101]
        mcp4161 = MCP4161(mock_spi)

        self.assertEqual(mcp4161.read(0b1010), 0b101010101)
        mock_spi.transfer.assert_called_once_with([0b10101111, 0b11111111])

    def test_write(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[0],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111, 0b11111111]
        mcp4161 = MCP4161(mock_spi)

        mcp4161.write(0b1010, 0b101010101)
        mock_spi.transfer.assert_called_once_with([0b10100001, 0b01010101])

    def test_increment(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[0],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111]
        mcp4161 = MCP4161(mock_spi)

        mcp4161.increment(MemoryAddress.VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00000100])
        mock_spi.transfer.reset_mock()
        mcp4161.increment(MemoryAddress.NON_VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00100100])

    def test_decrement(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[0],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111]
        mcp4161 = MCP4161(mock_spi)

        mcp4161.decrement(MemoryAddress.VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00001000])
        mock_spi.transfer.reset_mock()
        mcp4161.decrement(MemoryAddress.NON_VOLATILE_WIPER_0)
        mock_spi.transfer.assert_called_once_with([0b00101000])

    def test_set_wiper_step(self) -> None:
        mock_spi = MagicMock(
            mode=MCP4161.SPI_MODES[0],
            max_speed=MCP4161.MAX_SPI_MAX_SPEED,
            bit_order=MCP4161.SPI_BIT_ORDER,
            bits_per_word=MCP4161.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer.return_value = [0b11111111, 0b11111111]
        mcp4161 = MCP4161(mock_spi)

        for step in MCP4161.STEP_RANGE:
            mcp4161.set_volatile_wiper_step(step)
            mock_spi.transfer.assert_called_once_with(
                [step >> 8, step & ((1 << 8) - 1)],
            )
            mock_spi.transfer.reset_mock()
            mcp4161.set_non_volatile_wiper_step(step)
            mock_spi.transfer.assert_called_once_with(
                [0b00100000 | (step >> 8), step & ((1 << 8) - 1)],
            )
            mock_spi.transfer.reset_mock()


if __name__ == '__main__':
    main()  # pragma: no cover

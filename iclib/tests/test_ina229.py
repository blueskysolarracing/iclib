from unittest import TestCase, main
from unittest.mock import MagicMock

from iclib.ina229 import INA229


class INA229TestCase(TestCase):
    def test_read_register(self) -> None:
        alert_gpio = MagicMock()
        mock_spi = MagicMock(
            mode=INA229.SPI_MODE,
            max_speed=INA229.MAX_SPI_MAX_SPEED,
            bit_order=INA229.SPI_BIT_ORDER,
            bits_per_word=INA229.SPI_WORD_BIT_COUNT,
            extra_flags=0,
            transfer=lambda data: [0x00] * len(data),
        )
        maximum_expected_current = 60
        R_SHUNT = 0.01

        INA229(alert_gpio, mock_spi, maximum_expected_current, R_SHUNT)


if __name__ == '__main__':
    main()  # pragma: no cover

from unittest import TestCase, main
from unittest.mock import MagicMock

from iclib.ina229 import INA229


class INA229TestCase(TestCase):
    def test_read_register(self) -> None:
        R_SHUNT = 100
        alert_gpio = MagicMock()
        mock_spi = MagicMock(
            mode=INA229.SPI_MODE,
            max_speed=INA229.MAX_SPI_MAX_SPEED,
            bit_order=INA229.SPI_BIT_ORDER,
            bits_per_word=INA229.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )

        INA229(R_SHUNT, alert_gpio, mock_spi)


if __name__ == '__main__':
    main()  # pragma: no cover

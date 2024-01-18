from unittest import TestCase
from unittest.mock import MagicMock
from typing import ClassVar

from iclib.adc78h89 import ADC78H89


class ADC78H89TestCase(TestCase):
    INPUT_CHANNEL_MULTIPLIER: ClassVar[int] = (
        ADC78H89.DIVISOR // len(tuple(ADC78H89.InputChannel))
    )

    def test_sample_all(self) -> None:
        previous_input_channel = ADC78H89.DEFAULT_INPUT_CHANNEL

        def mock_sampling(input_channel: ADC78H89.InputChannel) -> int:
            nonlocal previous_input_channel

            if previous_input_channel == ADC78H89.InputChannel.GROUND:
                voltage = 0
            else:
                voltage = (
                    self.INPUT_CHANNEL_MULTIPLIER * previous_input_channel
                )

            previous_input_channel = input_channel

            return voltage

        def mock_transfer(transmitted_data: list[int]) -> list[int]:
            self.assertEqual(len(transmitted_data) % 2, 0)

            received_data = []

            for i, datum in enumerate(transmitted_data):
                if i % 2 == 0:
                    voltage = mock_sampling(ADC78H89.InputChannel(datum >> 3))

                    received_data.append(
                        voltage >> ADC78H89.SPI_WORD_BIT_COUNT,
                    )
                    received_data.append(
                        voltage & ((1 << ADC78H89.SPI_WORD_BIT_COUNT) - 1),
                    )
                else:
                    self.assertEqual(datum, 0)

            self.assertEqual(len(transmitted_data), len(received_data))

            return received_data

        mock_spi = MagicMock(
            mode=ADC78H89.SPI_MODES[-1],
            max_speed=ADC78H89.MIN_SPI_MAX_SPEED,
            bit_order=ADC78H89.SPI_BIT_ORDER,
            bits_per_word=ADC78H89.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer = mock_transfer
        adc78h89 = ADC78H89(mock_spi)
        voltages = adc78h89.sample_all()

        self.assertEqual(len(voltages), len(tuple(ADC78H89.InputChannel)))

        for key, value in voltages.items():
            self.assertIn(key, ADC78H89.InputChannel)

            if key == ADC78H89.InputChannel.GROUND:
                self.assertEqual(value, 0)
            else:
                self.assertAlmostEqual(
                    value,
                    ADC78H89.REFERENCE_VOLTAGE
                    * self.INPUT_CHANNEL_MULTIPLIER
                    * key
                    / ADC78H89.DIVISOR,
                )

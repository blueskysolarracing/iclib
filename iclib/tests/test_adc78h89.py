from random import random
from typing import ClassVar
from unittest import TestCase, main
from unittest.mock import MagicMock

from iclib.adc78h89 import ADC78H89, InputChannel


class ADC78H89TestCase(TestCase):
    VOLTAGES: ClassVar[dict[InputChannel, float]] = {
        input_channel: (
            0 if input_channel == InputChannel.GROUND else random()
        ) for input_channel in InputChannel
    }
    REFERENCE_VOLTAGE: ClassVar[float] = 3.3

    def test_input_channels(self) -> None:
        table = [
            [0, 0, 0, 'AIN1'],
            [0, 0, 1, 'AIN2'],
            [0, 1, 0, 'AIN3'],
            [0, 1, 1, 'AIN4'],
            [1, 0, 0, 'AIN5'],
            [1, 0, 1, 'AIN6'],
            [1, 1, 0, 'AIN7'],
            [1, 1, 1, 'GROUND'],
        ]

        self.assertEqual(
            table,
            [
                [
                    InputChannel.AIN1.ADD2,
                    InputChannel.AIN1.ADD1,
                    InputChannel.AIN1.ADD0,
                    InputChannel.AIN1.name,
                ],
                [
                    InputChannel.AIN2.ADD2,
                    InputChannel.AIN2.ADD1,
                    InputChannel.AIN2.ADD0,
                    InputChannel.AIN2.name,
                ],
                [
                    InputChannel.AIN3.ADD2,
                    InputChannel.AIN3.ADD1,
                    InputChannel.AIN3.ADD0,
                    InputChannel.AIN3.name,
                ],
                [
                    InputChannel.AIN4.ADD2,
                    InputChannel.AIN4.ADD1,
                    InputChannel.AIN4.ADD0,
                    InputChannel.AIN4.name,
                ],
                [
                    InputChannel.AIN5.ADD2,
                    InputChannel.AIN5.ADD1,
                    InputChannel.AIN5.ADD0,
                    InputChannel.AIN5.name,
                ],
                [
                    InputChannel.AIN6.ADD2,
                    InputChannel.AIN6.ADD1,
                    InputChannel.AIN6.ADD0,
                    InputChannel.AIN6.name,
                ],
                [
                    InputChannel.AIN7.ADD2,
                    InputChannel.AIN7.ADD1,
                    InputChannel.AIN7.ADD0,
                    InputChannel.AIN7.name,
                ],
                [
                    InputChannel.GROUND.ADD2,
                    InputChannel.GROUND.ADD1,
                    InputChannel.GROUND.ADD0,
                    InputChannel.GROUND.name,
                ],
            ],
        )

    def test_sample_all(self) -> None:
        previous_input_channel = ADC78H89.DEFAULT_INPUT_CHANNEL

        def mock_sample(input_channel: InputChannel) -> float:
            nonlocal previous_input_channel

            voltage = self.VOLTAGES[previous_input_channel]
            previous_input_channel = input_channel

            return voltage

        def mock_transfer(received_data_bytes: list[int]) -> list[int]:
            self.assertEqual(len(received_data_bytes) % 2, 0)

            transmitted_data_bytes = []

            for i, data_byte in enumerate(received_data_bytes):
                if i % 2 == 0:
                    voltage = mock_sample(InputChannel(data_byte >> 3))
                    data = round(
                        (
                            voltage
                            / self.REFERENCE_VOLTAGE
                            * ADC78H89.DIVISOR
                        ),
                    )

                    transmitted_data_bytes.append(
                        data >> ADC78H89.SPI_WORD_BIT_COUNT,
                    )
                    transmitted_data_bytes.append(
                        data & ((1 << ADC78H89.SPI_WORD_BIT_COUNT) - 1),
                    )
                else:
                    self.assertEqual(data_byte, 0)

            self.assertEqual(
                len(transmitted_data_bytes),
                len(received_data_bytes),
            )

            return transmitted_data_bytes

        mock_spi = MagicMock(
            mode=ADC78H89.SPI_MODE,
            max_speed=ADC78H89.MIN_SPI_MAX_SPEED,
            bit_order=ADC78H89.SPI_BIT_ORDER,
            bits_per_word=ADC78H89.SPI_WORD_BIT_COUNT,
            extra_flags=0,
        )
        mock_spi.transfer = mock_transfer
        adc78h89 = ADC78H89(mock_spi, self.REFERENCE_VOLTAGE)
        voltages = adc78h89.sample_all()

        self.assertEqual(len(voltages), len(tuple(InputChannel)))

        for key, value in voltages.items():
            self.assertIn(key, InputChannel)
            self.assertAlmostEqual(value, self.VOLTAGES[key], 3)


if __name__ == '__main__':
    main()  # pragma: no cover

from unittest import TestCase, main
from unittest.mock import MagicMock

from iclib.sn74hcs137 import Address, SN74HCS137


class SN74HCS137TestCase(TestCase):
    def test_address(self) -> None:
        for i in range(8):
            self.assertEqual(Address(i).name, f'Y{i}')

        self.assertEqual(
            [
                [False, False, False],
                [False, False, True],
                [False, True, False],
                [False, True, True],
                [True, False, False],
                [True, False, True],
                [True, True, False],
                [True, True, True],
            ],
            [
                [Address.Y0.A2, Address.Y0.A1, Address.Y0.A0],
                [Address.Y1.A2, Address.Y1.A1, Address.Y1.A0],
                [Address.Y2.A2, Address.Y2.A1, Address.Y2.A0],
                [Address.Y3.A2, Address.Y3.A1, Address.Y3.A0],
                [Address.Y4.A2, Address.Y4.A1, Address.Y4.A0],
                [Address.Y5.A2, Address.Y5.A1, Address.Y5.A0],
                [Address.Y6.A2, Address.Y6.A1, Address.Y6.A0],
                [Address.Y7.A2, Address.Y7.A1, Address.Y7.A0],
            ],
        )

    def test_api(self) -> None:
        latch_enable_gpio = MagicMock(direction='out', inverted=True)
        strobe_input_0_gpio = MagicMock(direction='out', inverted=False)
        strobe_input_1_gpio = MagicMock(direction='out', inverted=True)
        address_select_0_gpio = MagicMock(direction='out', inverted=False)
        address_select_1_gpio = MagicMock(direction='out', inverted=False)
        address_select_2_gpio = MagicMock(direction='out', inverted=False)
        sn74hcs137 = SN74HCS137(
            latch_enable_gpio,
            strobe_input_0_gpio,
            strobe_input_1_gpio,
            address_select_0_gpio,
            address_select_1_gpio,
            address_select_2_gpio,
        )

        sn74hcs137.enable_latch()
        latch_enable_gpio.write.assert_called_with(False)
        sn74hcs137.disable_latch()
        latch_enable_gpio.write.assert_called_with(True)

        for address in Address:
            sn74hcs137.select(address)
            strobe_input_0_gpio.write.assert_called_with(True)
            strobe_input_1_gpio.write.assert_called_with(True)
            address_select_0_gpio.write.assert_called_with(address.A0)
            address_select_1_gpio.write.assert_called_with(address.A1)
            address_select_2_gpio.write.assert_called_with(address.A2)

        sn74hcs137.deselect()
        strobe_input_0_gpio.write.assert_called_with(False)
        strobe_input_1_gpio.write.assert_called_with(False)


if __name__ == '__main__':
    main()  # pragma: no cover

from unittest import TestCase
from unittest.mock import call, MagicMock

from iclib.bno055 import BNO055, Register, OperationMode


class BNO055TestCase(TestCase):
    def test_read_register(self) -> None:
        mock_i2c = MagicMock()
        mock_gpio_out_imu_reset = MagicMock()
        mock_message = MagicMock()

        mock_message.data.return_value = [0b11111111]
        bno055 = BNO055(mock_i2c, mock_gpio_out_imu_reset)

        self.assertEqual(
            bno055.read(Register.ACC_DATA_X_LSB, 1),
            [0b11111111]
        )
        mock_message.assert_called_once_with(
            [Register.ACC_DATA_X_LSB] + [0], read=True
        )
        mock_i2c.transfer.assert_called_once_with(0x28, mock_message)
        mock_i2c.reset_mock()

        self.assertEqual(
            bno055.read(Register.QUA_DATA_Y_MSB, 1),
            [0b11111111]
        )
        mock_message.assert_called_once_with(
            [Register.QUA_DATA_W_LSB] + [0], read=True
        )
        mock_i2c.transfer.assert_called_once_with(0x28, mock_message)
        mock_i2c.reset_mock()

    def test_write_register(self) -> None:
        mock_i2c = MagicMock()
        mock_gpio_out_imu_reset = MagicMock()
        mock_message = MagicMock()

        mock_message.data.return_value = [0b11111111]
        bno055 = BNO055(mock_i2c, mock_gpio_out_imu_reset)

        self.assertEqual(
            bno055.write(Register.GRV_DATA_X_LSB, 1),
            [1]
        )

        mock_message.assert_called_once_with(
            [Register.GRV_DATA_X_LSB, 1], read=False
        )
        mock_i2c.transfer.assert_called_once_with(0x28, mock_message)
        mock_i2c.reset_mock()

        self.assertEqual(
            bno055.write(Register.EUL_DATA_Y_LSB, 1),
            [1]
        )
        mock_message.assert_called_once_with(
            [Register.EUL_DATA_Y_LSB, 1], read=False
        )
        mock_i2c.transfer.assert_called_once_with(0x28, mock_message)
        mock_i2c.reset_mock()

    def test_set_operation_mode(self) -> None:
        mock_i2c = MagicMock()
        mock_gpio_out_imu_reset = MagicMock()
        mock_message = MagicMock()
        bno055 = BNO055(mock_i2c, mock_gpio_out_imu_reset)
        bno055.write = MagicMock()

        bno055.select_operation_mode(True, True, True)
        mock_message.assert_called_once_with(
            [Register.OPR_MODE, OperationMode.AMG], read=False
        )

        mock_i2c.transfer.assert_called_once_with(0x28, mock_message)
        mock_i2c.reset_mock()

    def test_quaternion(self) -> None:
        mock_i2c = MagicMock()
        mock_gpio_out_imu_reset = MagicMock()
        bno055 = BNO055(mock_i2c, mock_gpio_out_imu_reset)
        bno055.read = MagicMock()

        bno055.quaternion()

        self.assertEqual(bno055.read.call_count, 8)
        expected_calls = [
            call(Register.QUA_DATA_W_MSB, 1),
            call(Register.QUA_DATA_W_LSB, 1),
            call(Register.QUA_DATA_X_MSB, 1),
            call(Register.QUA_DATA_X_LSB, 1),
            call(Register.QUA_DATA_Y_MSB, 1),
            call(Register.QUA_DATA_Y_LSB, 1),
            call(Register.QUA_DATA_Z_MSB, 1),
            call(Register.QUA_DATA_Z_LSB, 1),
        ]
        self.assertEqual(bno055.read.call_args_list, expected_calls)
        bno055.read.reset_mock()

    def test__get_vector(self) -> None:
        mock_i2c = MagicMock()
        mock_gpio_out_imu_reset = MagicMock()
        bno055 = BNO055(mock_i2c, mock_gpio_out_imu_reset)
        bno055.read = MagicMock()

        bno055._get_vector(
            Register.GYR_DATA_X_MSB,
            Register.GYR_DATA_X_LSB,
            Register.GYR_DATA_Y_MSB,
            Register.GYR_DATA_Y_LSB,
            Register.GYR_DATA_Z_MSB,
            Register.GYR_DATA_Z_LSB,
            16
        )

        self.assertEqual(bno055.read.call_count, 6)

    def test_magnetic_field(self) -> None:
        mock_i2c = MagicMock()
        mock_gpio_out_imu_reset = MagicMock()
        bno055 = BNO055(mock_i2c, mock_gpio_out_imu_reset)

        bno055.read = MagicMock()
        bno055._get_vector = MagicMock()

        bno055.magnetic_field()

        bno055._get_vector.assert_called_once_with(
            Register.MAG_DATA_X_MSB,
            Register.MAG_DATA_X_LSB,
            Register.MAG_DATA_Y_MSB,
            Register.MAG_DATA_Y_LSB,
            Register.MAG_DATA_Z_MSB,
            Register.MAG_DATA_Z_LSB,
            bno055.MAGNETIC_FIELD_UNIT_REPRESENTATION,
        )

        self.assertEqual(bno055.read.call_count, 6)
        expected_calls = [
            call(Register.MAG_DATA_X_MSB, 1),
            call(Register.MAG_DATA_X_LSB, 1),
            call(Register.MAG_DATA_Y_MSB, 1),
            call(Register.MAG_DATA_Y_LSB, 1),
            call(Register.QUA_DATA_Z_MSB, 1),
            call(Register.QUA_DATA_Z_LSB, 1),
        ]
        self.assertEqual(bno055.read.call_args_list, expected_calls)

        bno055._get_vector.reset_mock()
        bno055.read.reset_mock()

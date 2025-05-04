from unittest import TestCase
from unittest.mock import call, MagicMock
from periphery import I2C

from iclib.bno055 import BNO055, Register, OperationMode


class BNO055TestCase(TestCase):
    def test_read_register(self) -> None:
        mock_i2c = MagicMock()
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)

        self.assertEqual(bno055.read(Register.ACC_DATA_X_LSB, 1), [0])
        mock_i2c.transfer.assert_called_once_with(
            0x29,
            [
                mock_i2c.transfer.call_args.args[1][0],
                mock_i2c.transfer.call_args.args[1][1],
            ],
        )

    def test_write_register(self) -> None:
        mock_i2c = MagicMock(spec=I2C)
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)

        bno055.write(Register.GRV_DATA_X_LSB, 1)
        mock_i2c.transfer.assert_called_once_with(
            0x29,
            [mock_i2c.transfer.call_args.args[1][0]],
        )

    def test_close(self) -> None:
        mock_i2c = MagicMock()
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)

        bno055.close()

        mock_i2c.assert_has_calls([call.close()])
        mock_imu_reset_gpio.assert_has_calls([call.close()])

    def test_reset(self) -> None:
        mock_i2c = MagicMock()
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)

        bno055.reset()

        mock_imu_reset_gpio.assert_has_calls(
            [call.write(True), call.write(False)],
        )

    def test_set_operation_mode(self) -> None:
        mock_i2c = MagicMock()
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)
        bno055.write = MagicMock()  # type: ignore[method-assign]

        bno055.select_operation_mode(True, True, True)

        bno055.write.assert_called_once_with(
            Register.OPR_MODE,
            OperationMode.AMG,
        )

    def test_quaternion(self) -> None:
        mock_i2c = MagicMock()
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)
        bno055.read = MagicMock()  # type: ignore[method-assign]

        bno055.quaternion

        self.assertEqual(bno055.read.call_count, 8)
        self.assertEqual(
            bno055.read.call_args_list,
            [
                call(Register.QUA_DATA_W_MSB, 1),
                call(Register.QUA_DATA_W_LSB, 1),
                call(Register.QUA_DATA_X_MSB, 1),
                call(Register.QUA_DATA_X_LSB, 1),
                call(Register.QUA_DATA_Y_MSB, 1),
                call(Register.QUA_DATA_Y_LSB, 1),
                call(Register.QUA_DATA_Z_MSB, 1),
                call(Register.QUA_DATA_Z_LSB, 1),
            ],
        )

    def test__get_vector(self) -> None:
        mock_i2c = MagicMock(mode='out')
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)
        bno055.read = MagicMock()  # type: ignore[method-assign]

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
        mock_imu_reset_gpio = MagicMock(direction='out', inverted=True)
        bno055 = BNO055(mock_i2c, mock_imu_reset_gpio)
        bno055.read = MagicMock()  # type: ignore[method-assign]

        bno055.magnetic_field

        self.assertEqual(bno055.read.call_count, 6)
        self.assertEqual(
            bno055.read.call_args_list,
            [
                call(Register.MAG_DATA_X_MSB, 1),
                call(Register.MAG_DATA_X_LSB, 1),
                call(Register.MAG_DATA_Y_MSB, 1),
                call(Register.MAG_DATA_Y_LSB, 1),
                call(Register.MAG_DATA_Z_MSB, 1),
                call(Register.MAG_DATA_Z_LSB, 1),
            ],
        )

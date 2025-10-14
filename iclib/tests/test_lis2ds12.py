# import sys
# from unittest import TestCase
# from unittest.mock import MagicMock

# # Mock periphery module to avoid Windows fcntl dependency
# class MockI2C:
#     class Message:
#         def __init__(self, data, read=False):
#             self.data = data if isinstance(data, list) else list(data)
#             self.read = read

#     def __init__(self, *args, **kwargs):
#         pass

#     def transfer(self, addr, msgs):
#         pass


# class MockGPIO:
#     def __init__(self, *args, **kwargs):
#         pass

# # Mock the periphery module before any imports
# mock_periphery = MagicMock()
# mock_periphery.I2C = MockI2C
# mock_periphery.GPIO = MockGPIO
# sys.modules['periphery'] = mock_periphery

# from iclib.lis2ds12_nelson import (
#     LIS2DS12,
#     Register,
#     OutputDataRate,
#     FullScale,
#     CTRL1_BDU_MASK,
#     CTRL1_HF_ODR_MASK,
#     CTRL1_ODR_MASK,
#     CTRL1_ODR_SHIFT,
#     CTRL1_FS_MASK,
#     CTRL1_FS_SHIFT,
#     CTRL2_IF_ADD_INC_MASK,
# )

# class LIS2DS12TestCase(TestCase):
#     def setUp(self) -> None:
#         self.mock_i2c = MockI2C()

#         # emulate read sequences: WHO_AM_I, CTRL2 read, ... and raw burst
#         def xfer(addr, msgs):  # type: ignore[no-untyped-def]
#             # Simulate read transactions by checking for read=True messages
#             if len(msgs) == 2 and msgs[1].read:
#                 reg = msgs[0].data[0]
#                 if reg == Register.WHO_AM_I:
#                     msgs[1].data[:] = [LIS2DS12.DEVICE_ID]
#                 elif reg == Register.CTRL2:
#                     msgs[1].data[:] = [CTRL2_IF_ADD_INC_MASK]  # already set
#                 elif reg == Register.STATUS:
#                     msgs[1].data[:] = [0x01]
#                 elif reg == Register.OUT_X_L:
#                     msgs[1].data[:] = [0, 0, 0, 0, 0, 0]
#                 else:
#                     msgs[1].data[:] = [0x00] * len(msgs[1].data)
#             return None

#         self.mock_i2c.transfer = MagicMock(side_effect=xfer)

#     def test_init_configure(self) -> None:
#         dev = LIS2DS12(self.mock_i2c)
#         dev.init(
#             OutputDataRate.ODR_100_HZ,
#             FullScale.FS_4G,
#             discard_samples=1)

#         # Expected CTRL1 value
#         expected_ctrl1 = 0
#         expected_ctrl1 |= ((OutputDataRate.ODR_100_HZ.value
#                             << CTRL1_ODR_SHIFT) & CTRL1_ODR_MASK)
#         expected_ctrl1 |= ((FullScale.FS_4G.value
#                             << CTRL1_FS_SHIFT) & CTRL1_FS_MASK)
#         expected_ctrl1 |= CTRL1_BDU_MASK

#         # Find a transfer call that writes to CTRL1 and verify byte value
#         found = False
#         for args, _kwargs in [c for c in
#                               self.mock_i2c.transfer.call_args_list]:
#             addr, msgs = args
#             if addr != dev.address or not msgs:
#                 continue
#             msg = msgs[0]
#             if (hasattr(msg, 'data') and len(msg.data) >= 2 and
#                     msg.data[0] == Register.CTRL1):
#                 self.assertEqual(msg.data[1], expected_ctrl1)
#                 found = True
#                 break
#         self.assertTrue(found)

#     def test_configure_hf_odr(self) -> None:
#         dev = LIS2DS12(self.mock_i2c)
#         dev.init(
#             OutputDataRate.ODR_1600_HZ,
#             FullScale.FS_2G,
#             discard_samples=0)
#         # Expect HF bit set in CTRL1
#         expected_ctrl1 = 0
#         expected_ctrl1 |= ((OutputDataRate.ODR_1600_HZ.value
#                             << CTRL1_ODR_SHIFT) & CTRL1_ODR_MASK)
#         expected_ctrl1 |= ((FullScale.FS_2G.value << CTRL1_FS_SHIFT)
#                            & CTRL1_FS_MASK)
#         expected_ctrl1 |= CTRL1_BDU_MASK | CTRL1_HF_ODR_MASK
#         found = False
#         for args, _kwargs in [c for c in
#                               self.mock_i2c.transfer.call_args_list]:
#             addr, msgs = args
#             if addr != dev.address or not msgs:
#                 continue
#             msg = msgs[0]
#             if (hasattr(msg, 'data') and len(msg.data) >= 2 and
#                     msg.data[0] == Register.CTRL1):
#                 self.assertEqual(msg.data[1], expected_ctrl1)
#                 found = True
#                 break
#         self.assertTrue(found)

#     def test_read_accel(self) -> None:
#         dev = LIS2DS12(self.mock_i2c)
#         dev.init(discard_samples=0)
#         vec = dev.read_accel()
#         self.assertAlmostEqual(vec.x, 0.0)
#         self.assertAlmostEqual(vec.y, 0.0)
#         self.assertAlmostEqual(vec.z, 0.0)

# if __name__ == '__main__':
#     import unittest
#     unittest.main()

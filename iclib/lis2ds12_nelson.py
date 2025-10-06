"""LIS2DS12 3-axis accelerometer driver (I2C).

Production-focused Python driver using python-periphery.

Key notes (per datasheet snippets provided):
- WHO_AM_I (0x0F) must be 0x43.
- CTRL1 (0x20) fields: ODR[7:4], FS[3:2], HF_ODR[1], BDU[0].
- ODR tables:
    * LP: 1–800 Hz → ODR nibble 0x8–0xF (HF_ODR=0)
    * HR: 12.5–800 Hz → ODR nibble 0x1–0x7 (HF_ODR=0)
    * HF: 1.6–6.4 kHz → ODR nibble 0x5–0x7 with HF_ODR=1
- CTRL2 (0x21): SOFT_RESET, BOOT, IF_ADD_INC (set to 1), FDS_SLOPE,
    I2C_DISABLE, SIM, FUNC_CFG_EN.
    Do not enable FUNC_CFG_EN for normal operation.
- FIFO: configure via FIFO_CTRL (0x25) and FIFO_THS (0x2E);
    read FIFO_SRC (0x2F), FIFO_SAMPLES (0x30).
    Route FTH to INT1/INT2 via CTRL4/CTRL5.
- Data registers: burst read 0x28..0x2D with IF_ADD_INC=1 and BDU=1.

This driver purposely manages resolution exclusively via CTRL1/HF_ODR and does
not misuse CTRL2/CTRL4 for HR/HF.
"""

from dataclasses import dataclass
from enum import IntEnum
from logging import getLogger
from time import sleep
from typing import ClassVar, Dict, Optional, Tuple

from periphery import I2C, GPIO
from utilities import twos_complement  # type: ignore[import-not-found]

_logger = getLogger(__name__)


class Register(IntEnum):
    SENSORHUB1_REG = 0x06
    SENSORHUB2_REG = 0x07
    SENSORHUB3_REG = 0x08
    SENSORHUB4_REG = 0x09
    SENSORHUB5_REG = 0x0A
    SENSORHUB6_REG = 0x0B
    """Sensor hub output registers for external sensor data."""

    MODULE_8BIT = 0x0C
    """Module output value register."""

    WHO_AM_I = 0x0F
    """Device identification register."""

    CTRL1 = 0x20
    CTRL2 = 0x21
    CTRL3 = 0x22
    CTRL4 = 0x23
    CTRL5 = 0x24
    """Control registers for device configuration and interrupt settings."""

    FIFO_CTRL = 0x25
    """FIFO control register."""

    OUT_T = 0x26
    """Temperature sensor output register."""

    STATUS = 0x27
    """Status register for data ready and event flags."""

    OUT_X_L = 0x28
    OUT_X_H = 0x29
    OUT_Y_L = 0x2A
    OUT_Y_H = 0x2B
    OUT_Z_L = 0x2C
    OUT_Z_H = 0x2D
    """Acceleration data output registers (X, Y, Z axes, LSB and MSB)."""

    FIFO_THS = 0x2E
    FIFO_SRC = 0x2F
    FIFO_SAMPLES = 0x30
    """FIFO threshold, status, and sample count registers."""

    TAP_6D_THS = 0x31
    INT_DUR = 0x32
    WAKE_UP_THS = 0x33
    WAKE_UP_DUR = 0x34
    FREE_FALL = 0x35
    """Threshold and duration configuration registers for motion detection."""

    STATUS_DUP = 0x36
    WAKE_UP_SRC = 0x37
    TAP_SRC = 0x38
    SIX_D_SRC = 0x39
    """Event detection status and source registers."""

    STEP_COUNTER_MINTHS = 0x3A
    STEP_COUNTER_L = 0x3B
    STEP_COUNTER_H = 0x3C
    """Step counter configuration and output registers."""

    FUNC_CK_GATE = 0x3D
    FUNC_SRC = 0x3E
    FUNC_CTRL = 0x3F
    """Embedded function control and status registers."""


# Bit masks (only those verified/required are defined precisely)

# CTRL1 (0x20)
CTRL1_ODR_SHIFT: int = 4
CTRL1_ODR_MASK: int = 0xF0
CTRL1_FS_SHIFT: int = 2
CTRL1_FS_MASK: int = 0x0C
CTRL1_HF_ODR_MASK: int = 0x02
CTRL1_BDU_MASK: int = 0x01

# CTRL2 (0x21) — Bit positions vary by ST device family.
# From existing codebase and typical ST conventions, IF_ADD_INC was set
# with 0x02. We keep these masks conservative and only use
# IF_ADD_INC/RESET/BOOT in code.
CTRL2_SOFT_RESET_MASK: int = 0x40
CTRL2_BOOT_MASK: int = 0x80
CTRL2_IF_ADD_INC_MASK: int = 0x08
CTRL2_FDS_SLOPE_MASK: int = 0x10
CTRL2_I2C_DISABLE_MASK: int = 0x04
CTRL2_SIM_MASK: int = 0x01
CTRL2_FUNC_CFG_EN_MASK: int = 0x20

# STATUS (0x27) — return raw; flags may be checked by user/project.
# Provide a generic DRDY bit mask as 0x01 (common pattern), but expose
# raw too.
STATUS_DRDY_MASK: int = 0x01

# CTRL4 (0x23) — ST[2:1] controls self-test
CTRL4_ST_POS_MASK:         int = 0x02  # ST1=1, ST2=0 => positive ST
CTRL4_ST_NEG_MASK:         int = 0x04  # ST2=1, ST1=0 => negative ST
CTRL4_ST_CLEAR_MASK:       int = 0x06  # both ST bits

# FIFO masks — expose raw fields; write helpers accept raw mode/threshold
# values. Users should pass correct mode values per datasheet; we don't
# hardcode mapping.
FIFO_MODE_MASK: int = 0xFF     # Pass-through write to FIFO_CTRL
FIFO_THS_MASK: int = 0xFF      # Pass-through threshold value


# Exceptions & utilities

class LIS2DS12Error(Exception):
    """Base class for LIS2DS12 errors."""


class DeviceNotFoundError(LIS2DS12Error):
    """Raised when WHO_AM_I doesn't match expected device ID."""


class I2CTransferError(LIS2DS12Error):
    """Raised when I2C communication fails after retries."""


def _set_field(value: int, mask: int, shift: int, field: int) -> int:
    """Set a bitfield.

    :param value: Original register value.
    :param mask: Bit mask for the field.
    :param shift: Field shift.
    :param field: Field value (unshifted).
    :return: New value.
    """
    return (value & ~mask) | ((field << shift) & mask)


class OutputDataRate(IntEnum):
    POWER_DOWN = 0x0
    ODR_1_HZ = 0x8
    ODR_12_5_HZ = 0x9
    ODR_25_HZ = 0xA
    ODR_50_HZ = 0xB
    ODR_100_HZ = 0xC
    ODR_200_HZ = 0xD
    ODR_400_HZ = 0xE
    ODR_800_HZ = 0xF
    ODR_12_5_HZ_HR = 0x1
    ODR_25_HZ_HR = 0x2
    ODR_50_HZ_HR = 0x3
    ODR_100_HZ_HR = 0x4
    ODR_200_HZ_HR = 0x5
    ODR_400_HZ_HR = 0x6
    ODR_800_HZ_HR = 0x7
    ODR_1600_HZ = 0x5
    ODR_3200_HZ = 0x6
    ODR_6400_HZ = 0x7


class FullScale(IntEnum):
    FS_2G = 0x0
    FS_16G = 0x1
    FS_4G = 0x2
    FS_8G = 0x3


@dataclass
class LIS2DS12:
    """High-level driver class for LIS2DS12.

    Constructor is lightweight; call `init()` to configure the device.
    """

    DEVICE_ID: ClassVar[int] = 0x43

    i2c: I2C
    address: int = 0x1E  # SA0=GND → 0x1E; SA0=Vdd → 0x1D
    int1: Optional[GPIO] = None
    int2: Optional[GPIO] = None
    i2c_retries: int = 3
    i2c_retry_delay_s: float = 0.001
    _last_odr: OutputDataRate = OutputDataRate.ODR_100_HZ
    _last_fs: FullScale = FullScale.FS_2G

    @dataclass
    class Vector:
        x: float
        y: float
        z: float

    # --------------------- Low-level I2C helpers with retry ------------------

    def _xfer(self, messages: list[I2C.Message]) -> None:
        """Perform an I2C transfer with retries.

        :raises I2CTransferError: when transfer repeatedly fails.
        """
        last_exc: Exception | None = None
        for _ in range(self.i2c_retries):
            try:
                self.i2c.transfer(self.address, messages)
                return
            except Exception as exc:  # pragma: no cover (depends on HW)
                last_exc = exc
                sleep(self.i2c_retry_delay_s)
        raise I2CTransferError(str(last_exc))

    def write(self, register: Register, data: int) -> None:
        """Write 1 byte to a register."""
        self._xfer([I2C.Message([register, data])])

    def read(self, register: Register, length: int) -> list[int]:
        """Read `length` bytes starting from `register` (auto-increment)."""
        write_message = I2C.Message([register])
        read_message = I2C.Message([0] * length, read=True)
        self._xfer([write_message, read_message])
        return list(read_message.data)

    # --------------------------- Initialization flow -------------------------

    def init(
        self,
        odr: OutputDataRate = OutputDataRate.ODR_100_HZ,
        fs: FullScale = FullScale.FS_2G,
        discard_samples: int = 4,
    ) -> None:
        """Initialize and configure the device.

        Steps:
        1) Soft-reset and wait
        2) Verify WHO_AM_I
        3) Ensure IF_ADD_INC=1 for burst auto-increment
        4) Configure CTRL1: ODR, FS, HF_ODR (if high-frequency), BDU=1
        5) Discard first N samples after ODR change
        """
        self.soft_reset()
        sleep(0.01)

        who = self.read(Register.WHO_AM_I, 1)[0]
        if who != self.DEVICE_ID:
            raise DeviceNotFoundError(
                f"Unexpected WHO_AM_I: 0x{who:02X} "
                f"(expected 0x{self.DEVICE_ID:02X})"
            )

        # Ensure I2C auto-increment.
        self._set_ctrl2_bits(CTRL2_IF_ADD_INC_MASK, True)

        # Configure CTRL1 with requested ODR/FS and BDU=1.
        self.configure(odr, fs)

        # Discard a few samples to allow filters/ODR to settle.
        for _ in range(discard_samples):
            try:
                _ = self.read_raw()
            except LIS2DS12Error:
                break

    def reinit(self) -> None:
        """Re-apply configuration (for bus resets or power transitions)."""
        self.init(self._last_odr, self._last_fs)

    def soft_reset(self) -> None:
        """Trigger a software reset and wait a short time."""
        # Keep IF_ADD_INC untouched by setting only reset bit (write-1 action).
        try:
            current = self.read(Register.CTRL2, 1)[0]
        except LIS2DS12Error:
            current = 0
        self.write(Register.CTRL2, current | CTRL2_SOFT_RESET_MASK)
        sleep(0.01)

    def boot(self) -> None:
        """Trigger a memory reboot (boot sequence)."""
        current = self.read(Register.CTRL2, 1)[0]
        self.write(Register.CTRL2, current | CTRL2_BOOT_MASK)
        sleep(0.01)

    def _set_ctrl2_bits(self, mask: int, enable: bool) -> None:
        current = self.read(Register.CTRL2, 1)[0]
        new_val = (current | mask) if enable else (current & ~mask)
        self.write(Register.CTRL2, new_val)

    # ------------------------------- Configure -------------------------------

    def configure(self, odr: OutputDataRate, fs: FullScale) -> None:
        """Configure ODR/FS/HF_ODR/BDU via CTRL1 only.

        - Sets BDU=1 (coherent multi-byte reads)
        - Computes HF_ODR based on the selected ODR (for 1.6–6.4 kHz)
        """
        ctrl1 = 0

        # ODR nibble
        ctrl1 = _set_field(ctrl1, CTRL1_ODR_MASK, CTRL1_ODR_SHIFT, odr.value)

        # FS bits
        ctrl1 = _set_field(ctrl1, CTRL1_FS_MASK, CTRL1_FS_SHIFT, fs.value)

        # HF_ODR for high-frequency rates
        if odr in (OutputDataRate.ODR_1600_HZ,
                   OutputDataRate.ODR_3200_HZ,
                   OutputDataRate.ODR_6400_HZ):
            ctrl1 |= CTRL1_HF_ODR_MASK

        # BDU on
        ctrl1 |= CTRL1_BDU_MASK

        self.write(Register.CTRL1, ctrl1)
        self._last_odr = odr
        self._last_fs = fs

    def enable_highpass(self, enabled: bool) -> None:
        """Enable/disable high-pass slope filter via CTRL2.FDS_SLOPE.

        Note: Bit position requires datasheet confirmation for the target
        silicon.
        """
        self._set_ctrl2_bits(CTRL2_FDS_SLOPE_MASK, enabled)

    # --------------------------------- FIFO ----------------------------------

    def set_fifo(self, mode_raw: int, threshold: int) -> None:
        """Configure FIFO mode and threshold.

        This method accepts raw `mode_raw` as defined by the datasheet for
        FIFO_CTRL and a byte threshold for FIFO_THS. It does not translate
        symbolic modes to bit patterns to avoid incorrect assumptions.
        """
        self.write(Register.FIFO_CTRL, mode_raw & FIFO_MODE_MASK)
        self.write(Register.FIFO_THS, threshold & FIFO_THS_MASK)

    def read_fifo_src(self) -> int:
        return self.read(Register.FIFO_SRC, 1)[0]

    def read_fifo_samples(self) -> int:
        return self.read(Register.FIFO_SAMPLES, 1)[0]

    # ------------------------------- Interrupts ------------------------------
    # NOTE: Interrupt functionality commented out - INT1/INT2 pins not
    # accessible

    # def route_interrupts(
    #     self,
    #     drdy_to_int1: bool = True,
    #     fth_to_int1: bool = False,
    #     active_low: bool = False,
    #     open_drain: bool = False,
    #     latched: bool = False,
    # ) -> None:
    #     """Route events to INT1/INT2 and configure pin behavior.
    #
    #     NOTE: Exact bit positions in CTRL4/CTRL5 require datasheet
    #     validation. This method is present for API completeness and
    #     should be finalized with the actual silicon reference.
    #     """
    #     _logger.debug(
    #         "route_interrupts(drdy_to_int1=%s, fth_to_int1=%s, "
    #         "active_low=%s, open_drain=%s, latched=%s)",
    #         drdy_to_int1, fth_to_int1, active_low, open_drain, latched,
    #     )
    #     # Placeholder: read-modify-write preserved for future bit routing
    #     ctrl4 = self.read(Register.CTRL4, 1)[0]
    #     ctrl5 = self.read(Register.CTRL5, 1)[0]
    #     # TODO: apply bitfields per datasheet
    #     self.write(Register.CTRL4, ctrl4)
    #     self.write(Register.CTRL5, ctrl5)

    # def wait_for_drdy(self, timeout_ms: int = 10) -> bool:
    #     """Wait for DRDY via INT1 GPIO if provided, else poll STATUS.
    #
    #     :return: True if data ready occurred before timeout, else False.
    #     """
    #     if self.int1 is not None:
    #         # Assume INT1 configured as data-ready; GPIO edge configured
    #         # externally.
    #         return bool(self.int1.poll(timeout_ms / 1000.0))
    #     # Fallback: poll STATUS register
    #     end = timeout_ms / 1000.0
    #     t = 0.0
    #     step = 0.001
    #     while t < end:
    #         if self.status() & STATUS_DRDY_MASK:
    #             return True
    #         sleep(step)
    #         t += step
    #     return False

    # def wait_for_fifo_fth(self, timeout_ms: int = 10) -> bool:
    #     if self.int1 is not None:
    #         return bool(self.int1.poll(timeout_ms / 1000.0))
    #     end = timeout_ms / 1000.0
    #     t = 0.0
    #     step = 0.001
    #     while t < end:
    #         src = self.read_fifo_src()
    #         # TODO: check FTH flag bit in FIFO_SRC
    #         if src:  # any non-zero as placeholder
    #             return True
    #         sleep(step)
    #         t += step
    #     return False

    # ------------------------------- Data path -------------------------------

    def read_raw(self) -> Tuple[int, int, int]:
        """Burst-read raw 16-bit X/Y/Z (two's complement).

        Requires IF_ADD_INC=1 and BDU=1 for coherent reads.
        """
        data = self.read(Register.OUT_X_L, 6)
        x = (data[1] << 8) | data[0]
        y = (data[3] << 8) | data[2]
        z = (data[5] << 8) | data[4]
        # two's complement for 16-bit
        x = twos_complement(x, 16)
        y = twos_complement(y, 16)
        z = twos_complement(z, 16)
        return x, y, z

    @staticmethod
    def convert_to_g(
        raw: Tuple[int, int, int],
        fs: FullScale
    ) -> Tuple[float, float, float]:
        """Convert raw counts to g using nominal sensitivity for FS.

        Sensitivities (approx, typical for LIS2DS12 HR mode):
        - ±2g  → 0.061 mg/LSB
        - ±4g  → 0.122 mg/LSB
        - ±8g  → 0.244 mg/LSB
        - ±16g → 0.488 mg/LSB

        Returned values are in g.
        """
        sens_mg_per_lsb = {
            FullScale.FS_2G: 0.061,
            FullScale.FS_4G: 0.122,
            FullScale.FS_8G: 0.244,
            FullScale.FS_16G: 0.488,
        }[fs]
        scale = sens_mg_per_lsb / 1000.0
        x, y, z = raw
        return x * scale, y * scale, z * scale

    def read_accel(self) -> "LIS2DS12.Vector":
        """Read acceleration vector in g."""
        raw = self.read_raw()
        xg, yg, zg = self.convert_to_g(raw, self._last_fs)
        return self.Vector(xg, yg, zg)

    def read_temperature(self) -> float:
        """
        Read temperature in °C.

        According to LIS2DS12 datasheet:
        - OUT_T is 8-bit two's complement.
        - Sensitivity = 1 °C/LSB.
        - 0 LSB corresponds to 25 °C.
        """
        t = self.read(Register.OUT_T, 1)[0]
        if t & 0x80:  # sign extension for negative values
            t -= 0x100
        return 25.0 + float(t)  # °C

    # ------------------------------ Status & health --------------------------

    def status(self) -> int:
        """Return raw STATUS register value."""
        return self.read(Register.STATUS, 1)[0]

    def fifo_status(self) -> Dict[str, int]:
        """Return FIFO status information.

        Returns a dict with raw fields so higher-level logic can decide
        based on the actual silicon bit definitions and usage.
        """
        return {
            "FIFO_SRC": self.read_fifo_src(),
            "FIFO_SAMPLES": self.read_fifo_samples(),
        }

    def self_test(self) -> None:
        """Perform self-test sequence per datasheet.

        Validates sensor functionality by comparing baseline readings with
        readings taken during self-test mode. Delta must be within
        70-1500 mg.
        """
        # save current config
        c1 = self.read(Register.CTRL1, 1)[0]
        c2 = self.read(Register.CTRL2, 1)[0]
        c4 = self.read(Register.CTRL4, 1)[0]

        try:
            # ensure IF_ADD_INC=1 (it defaults to 1 but set explicitly)
            self.write(
                Register.CTRL2,
                (c2 | CTRL2_IF_ADD_INC_MASK) & ~CTRL2_FUNC_CFG_EN_MASK
            )

            # HR 100 Hz, FS=±2g, BDU=1; ODR nibble=0b0100, FS=00, HF_ODR=0
            ctrl1 = (0b0100 << 4) | (0b00 << 2) | 0 | 1
            self.write(Register.CTRL1, ctrl1)

            # discard 1 sample for HR>=100Hz
            _ = self.read_raw()

            # collect baseline average (32 samples)
            fs = FullScale.FS_2G
            sx = sy = sz = 0.0
            for _ in range(32):
                raw = self.read_raw()
                x_g, y_g, z_g = self.convert_to_g(raw, fs)
                # convert to mg for comparison
                sx += x_g * 1000.0
                sy += y_g * 1000.0
                sz += z_g * 1000.0
            base = (sx / 32.0, sy / 32.0, sz / 32.0)

            # enable ST(+): ST1=1, ST2=0
            self.write(
                Register.CTRL4,
                (c4 & ~CTRL4_ST_CLEAR_MASK) | CTRL4_ST_POS_MASK
            )

            # settle; then discard 1 sample again
            sleep(0.08)
            _ = self.read_raw()

            # collect stimulated average (32 samples)
            sx = sy = sz = 0.0
            for _ in range(32):
                raw = self.read_raw()
                x_g, y_g, z_g = self.convert_to_g(raw, fs)
                # convert to mg for comparison
                sx += x_g * 1000.0
                sy += y_g * 1000.0
                sz += z_g * 1000.0
            stim = (sx / 32.0, sy / 32.0, sz / 32.0)

            # compute deltas and check window
            deltas = [abs(stim[i] - base[i]) for i in range(3)]
            for d in deltas:
                if not (70.0 <= d <= 1500.0):
                    raise ValueError(
                        f"Self-test out of spec: delta {d:.1f} mg"
                    )

        finally:
            # clear ST and restore config
            self.write(Register.CTRL4, c4 & ~CTRL4_ST_CLEAR_MASK)
            self.write(Register.CTRL1, c1)
            self.write(Register.CTRL2, c2)

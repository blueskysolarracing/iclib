from abc import ABC
from dataclasses import dataclass
from math import copysign
from struct import pack, unpack
from typing import ClassVar

from can import BusABC, Message


@dataclass
class MotorControlBroadcastMessage(ABC):
    MESSAGE_IDENTIFIER: ClassVar[int]
    FORMAT: ClassVar[str]


@dataclass
class IdentificationInformation(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x00
    FORMAT = '<II'
    prohelion_id: int
    serial_number: int


@dataclass
class StatusInformation(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x01
    FORMAT = '<HHHBB'
    limit_flags: int
    error_flags: int
    active_motor: int
    transmit_error_count: int
    receive_error_count: int


@dataclass
class BusMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x02
    FORMAT = '<ff'
    bus_voltage: float
    bus_current: float


@dataclass
class VelocityMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x03
    FORMAT = '<ff'
    motor_velocity: float
    vehicle_velocity: float


@dataclass
class PhaseCurrentMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x04
    FORMAT = '<ff'
    motor_velocity: float
    phase_c_current: float


@dataclass
class MotorVoltageVectorMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x05
    FORMAT = '<ff'
    Vq: float
    Vd: float


@dataclass
class MotorCurrentVectorMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x06
    FORMAT = '<ff'
    Iq: float
    Id: float


@dataclass
class MotorBackEMFMeasurementPrediction(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x07
    FORMAT = '<ff'
    BEMFq: float
    BEMFd: float


@dataclass
class VoltageRailMeasurement15V(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x08
    FORMAT = '<ff'
    reserved: float
    supply_15v: float


@dataclass
class VoltageRailMeasurement3_3VAnd1_9V(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x09
    FORMAT = '<ff'
    supply_1_9v: float
    supply_3_3v: float


@dataclass
class Reserved0(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x0A
    FORMAT = '<ff'
    reserved_2: float
    reserved_1: float


@dataclass
class HeatSinkAndMotorTemperatureMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x0B
    FORMAT = '<ff'
    motor_temp: float
    heat_sink_temp: float


@dataclass
class DSPBoardTemperatureMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x0C
    FORMAT = '<ff'
    dsp_board_temp: float
    reserved: float


@dataclass
class Reserved1(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x0D
    FORMAT = '<ff'
    reserved_2: float
    reserved_1: float


@dataclass
class OdometerAndBusAmpHoursMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x0E
    FORMAT = '<ff'
    odometer: float
    dc_bus_amphours: float


@dataclass
class SlipSpeedMeasurement(MotorControlBroadcastMessage):
    MESSAGE_IDENTIFIER = 0x17
    FORMAT = '<ff'
    reserved: float
    slip_speed: float


@dataclass
class WaveSculptor22:
    CAN_BUS_BITRATES: ClassVar[tuple[int, ...]] = (
        1000000,
        500000,
        250000,
        125000,
        100000,
        50000,
    )
    can_bus: BusABC
    driver_controls_base_address: int
    motor_controller_base_address: int

    def __post_init__(self) -> None:
        if self.driver_controls_base_address not in range(1 << 12):
            raise ValueError('invalid driver controls base address')

    def _send(
            self,
            message_identifier: int,
            data: bytes,
            timeout: float | None = None,
            base_address: int | None = None,
    ) -> None:
        if len(data) != 8:
            raise ValueError('data is not 8 bytes')

        if base_address is None:
            base_address = self.driver_controls_base_address

        arbitration_id = base_address + message_identifier
        message = Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=False,
        )

        self.can_bus.send(message, timeout)

    # Drive Commands

    def motor_drive(
            self,
            motor_current: float,
            motor_velocity: float,
            timeout: float | None = None,
    ) -> None:
        """Send the Motor Drive Command.

        :param motor_current: The ``Motor Current`` variable of the
                              percentage type.
        :param motor_velocity: The ``Motor Velocity`` variable of the
                               rpm type.
        :return: ``None``.
        """
        self._send(0x1, pack('<ff', motor_velocity, motor_current), timeout)

    def motor_power(
            self,
            bus_current: float,
            timeout: float | None = None,
    ) -> None:
        self._send(0x2, pack('<ff', 0, bus_current), timeout)

    def reset(self, timeout: float | None = None) -> None:
        self._send(0x3, pack('<ff', 0, 0), timeout)

    UNOBTAINABLE_VELOCITY: ClassVar[float] = 20000

    def motor_drive_torque_control_mode(
            self,
            motor_current: float,
            timeout: float | None = None,
    ) -> None:
        motor_velocity = copysign(self.UNOBTAINABLE_VELOCITY, motor_current)

        self.motor_drive(motor_current, motor_velocity, timeout)

    def motor_drive_velocity_control_mode(
            self,
            motor_velocity: float,
            motor_current: float = 1,
            timeout: float | None = None,
    ) -> None:
        self.motor_drive(motor_current, motor_velocity, timeout)

    # Motor Control Broadcast Messages

    MOTOR_CONTROL_BROADCAST_MESSAGE_TYPES: ClassVar[
            tuple[type[MotorControlBroadcastMessage], ...]
    ] = (
        IdentificationInformation,
        StatusInformation,
        BusMeasurement,
        VelocityMeasurement,
        PhaseCurrentMeasurement,
        MotorVoltageVectorMeasurement,
        MotorCurrentVectorMeasurement,
        MotorBackEMFMeasurementPrediction,
        VoltageRailMeasurement15V,
        VoltageRailMeasurement3_3VAnd1_9V,
        Reserved0,
        HeatSinkAndMotorTemperatureMeasurement,
        DSPBoardTemperatureMeasurement,
        Reserved1,
        OdometerAndBusAmpHoursMeasurement,
        SlipSpeedMeasurement,
    )

    def parse(self, message: Message) -> MotorControlBroadcastMessage | None:
        device_identifier = message.arbitration_id >> 5

        if self.motor_controller_base_address != device_identifier << 5:
            return None

        message_identifier = message.arbitration_id & ((1 << 5) - 1)
        broadcast_message = None

        for type_ in self.MOTOR_CONTROL_BROADCAST_MESSAGE_TYPES:
            if message_identifier == type_.MESSAGE_IDENTIFIER:
                broadcast_message = type_(*unpack(type_.FORMAT, message.data))

                break

        return broadcast_message

    # Configuration Commands

    CONFIGURATION_ACCESS_KEY: ClassVar[bytes] = b'ACTMOT'

    def active_motor_change(
            self,
            active_motor: int,
            timeout: float | None = None,
    ) -> None:
        if active_motor not in range(10):
            raise ValueError('invalid active motor')

        self._send(
            0x12,
            pack('<6sH', self.CONFIGURATION_ACCESS_KEY, active_motor),
            timeout,
            self.motor_controller_base_address,
        )

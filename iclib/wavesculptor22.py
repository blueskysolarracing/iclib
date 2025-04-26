from abc import ABC
from dataclasses import dataclass
from functools import cached_property
from math import copysign
from struct import pack, unpack
from typing import ClassVar

from can import BusABC, Message


@dataclass
class MotorControlBroadcastMessage(ABC):
    message_identifier: ClassVar[int]
    format_: ClassVar[str]


@dataclass
class IdentificationInformation(MotorControlBroadcastMessage):
    message_identifier = 0x00
    format_ = '<II'
    prohelion_id: int
    serial_number: int


@dataclass
class StatusInformation(MotorControlBroadcastMessage):
    message_identifier = 0x01
    format_ = '<HHHBB'
    limit_flags: int
    error_flags: int
    active_motor: int
    transmit_error_count: int
    receive_error_count: int


@dataclass
class BusMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x02
    format_ = '<ff'
    bus_voltage: float
    bus_current: float


@dataclass
class VelocityMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x03
    format_ = '<ff'
    motor_velocity: float
    vehicle_velocity: float


@dataclass
class PhaseCurrentMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x04
    format_ = '<ff'
    motor_velocity: float
    phase_c_current: float


@dataclass
class MotorVoltageVectorMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x05
    format_ = '<ff'
    Vq: float
    Vd: float


@dataclass
class MotorCurrentVectorMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x06
    format_ = '<ff'
    Iq: float
    Id: float


@dataclass
class MotorBackEMFMeasurementPrediction(MotorControlBroadcastMessage):
    message_identifier = 0x07
    format_ = '<ff'
    BEMFq: float
    BEMFd: float


@dataclass
class VoltageRailMeasurement15V(MotorControlBroadcastMessage):
    message_identifier = 0x08
    format_ = '<ff'
    reserved: float
    supply_15v: float


@dataclass
class VoltageRailMeasurement3_3VAnd1_9V(MotorControlBroadcastMessage):
    message_identifier = 0x09
    format_ = '<ff'
    supply_1_9v: float
    supply_3_3v: float


@dataclass
class Reserved0(MotorControlBroadcastMessage):
    message_identifier = 0x0A
    format_ = '<ff'
    reserved_2: float
    reserved_1: float


@dataclass
class HeatSinkAndMotorTemperatureMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x0B
    format_ = '<ff'
    motor_temp: float
    heat_sink_temp: float


@dataclass
class DSPBoardTemperatureMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x0C
    format_ = '<ff'
    dsp_board_temp: float
    reserved: float


@dataclass
class Reserved1(MotorControlBroadcastMessage):
    message_identifier = 0x0D
    format_ = '<ff'
    reserved_2: float
    reserved_1: float


@dataclass
class OdometerAndBusAmpHoursMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x0E
    format_ = '<ff'
    odometer: float
    dc_bus_amphours: float


@dataclass
class SlipSpeedMeasurement(MotorControlBroadcastMessage):
    message_identifier = 0x17
    format_ = '<ff'
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
    device_identifier: int

    def __post_init__(self) -> None:
        if self.device_identifier not in range(1 << 6):
            raise ValueError('invalid device identifier')

    @cached_property
    def driver_controls_base_address(self) -> int:
        return self.device_identifier << 5

    def _send(
            self,
            message_identifier: int,
            data: bytes,
            timeout: float | None = None,
    ) -> None:
        if len(data) != 8:
            raise ValueError('data is not 8 bytes')

        arbitration_id = self.driver_controls_base_address + message_identifier
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
        broadcast_message = None

        for type_ in self.MOTOR_CONTROL_BROADCAST_MESSAGE_TYPES:
            arbitration_id = (
                self.driver_controls_base_address
                + type_.message_identifier
            )

            if message.arbitration_id == arbitration_id:
                broadcast_message = type_(*unpack(type_.format_, message.data))

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
            pack('<6sH', self.CONFIGURATION_ACCESS_KEY, 5),
            timeout,
        )

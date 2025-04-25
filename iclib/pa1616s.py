from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum, IntEnum, StrEnum
from periphery import Serial
from typing import Any, cast, ClassVar


def calculate_checksum(nmea_string: str) -> int:
    """Calculates the checksum value of an NMEA sentence

    :param: The NMEA sentence string to calculate the checksum of.
    :return: The checksum value of the NMEA sentence as a base-10 int.
    """
    if nmea_string[0] == '$':
        nmea_body = nmea_string[1:]
    else:
        nmea_body = nmea_string

    if '*' in nmea_body:
        nmea_body = nmea_body[: nmea_body.index('*')]

    checksum = 0

    for char in nmea_body:
        checksum ^= ord(char)

    return checksum


class GPOutputSentence(ABC):
    """The abstract base class for update messages outputted
    by PA1616S ($GPXXX NMEA sentences).
    """

    MESSAGE_ID: ClassVar[str]
    """The NMEA message ID of the output sentence."""
    _STATIC_FIELD_SCHEMA: ClassVar[list[tuple[str, type[Any]]]]

    @classmethod
    def from_nmea_sentence(
            cls,
            nmea_sentence: str,
    ) -> GPOutputSentence | None:
        """Create a :class:`GPOutputSentence` object from an NMEA
        sentence string. Returns None if the sentence is not parsable.

        :param nmea_sentence: The NMEA sentence string to parse.
        :return: (Optional) The :class:`GPOutputSentence` object created
                 from the NMEA sentence.
        """
        new_output_sentence_obj = cls()
        split_NMEA_sentence = nmea_sentence.split(',')

        if split_NMEA_sentence[0] != cls.MESSAGE_ID:
            raise ValueError(
                (
                    f'Invalid NMEA sentence. Expected {cls.MESSAGE_ID} but'
                    f' received {split_NMEA_sentence[0]}'
                ),
            )

        given_checksum = int(split_NMEA_sentence[-1][1:])
        calculated_checksum = calculate_checksum(nmea_sentence)

        if given_checksum != calculated_checksum:
            raise ValueError(
                (
                    f'Invalid checksum. Expected {given_checksum} but received'
                    f' {calculated_checksum}'
                ),
            )

        for i, item in enumerate(cls._STATIC_FIELD_SCHEMA):
            field_name, field_type = item
            raw_field_value_str = split_NMEA_sentence[i + 1]

            if (
                issubclass(field_type, Enum)
                and raw_field_value_str not in field_type.__members__
            ):
                setattr(new_output_sentence_obj, field_name, None)
                continue

            setattr(
                new_output_sentence_obj,
                field_name,
                field_type(raw_field_value_str),
            )

        return new_output_sentence_obj


@dataclass
class GPLocationDataSentence(GPOutputSentence, ABC):
    """The abstract base class for location data outputted
    by PA1616S ($GPXXX NMEA sentences)."""

    _latitude: str | None = None
    _NS_indicator: str | None = None
    _longitude: str | None = None
    _EW_indicator: str | None = None

    @property
    def latitude(self) -> tuple[int, float, str]:
        """Latitude in (degrees, minutes, direction)"""
        assert self._latitude is not None
        assert self._NS_indicator is not None

        return (
            int(self._latitude[:2]),
            float(self._latitude[2:]),
            self._NS_indicator,
        )

    @property
    def longitude(self) -> tuple[int, float, str]:
        """Longitude in (degrees, minutes, direction)"""
        assert self._longitude is not None
        assert self._EW_indicator is not None

        return (
            int(self._longitude[:3]),
            float(self._longitude[3:]),
            self._EW_indicator,
        )


class GPMode(StrEnum):
    """Mode data transmitted by PA1616S in RMC and VTG mode. See table 8
    on datasheet.
    """

    AUTONOMOUS = 'A'
    """Autonomous mode"""
    DIFFERENTIAL = 'D'
    """Differential mode"""
    ESTIMATED = 'E'
    """Estimated mode"""


@dataclass
class GPGGA(GPLocationDataSentence):
    """Store field values that can be outputted by the GPS for $GPGGA
    update messages by the PA1616S module: Time, position, and fix type
    data. See table 2 on datasheet.
    """

    class PositionFixIndicator(IntEnum):
        """Position fix indicator data transmitted by PA1616S in GGA
        mode. See table 3 on datasheet.
        """

        NO_FIX = 0
        GPS_FIX = 1
        DIFFERENTIAL_GPS_FIX = 2

    MESSAGE_ID: ClassVar[str] = '$GPGGA'
    """The NMEA message ID for the GGA update message."""

    # See Table 2 on datasheet
    _STATIC_FIELD_SCHEMA: ClassVar[list[tuple[str, type]]] = [
        ('time', str),
        ('_latitude', str),
        ('_NS_indicator', str),
        ('_longitude', str),
        ('_EW_indicator', str),
        ('position_fix_indicator', PositionFixIndicator),
        ('satelites_used', int),
        ('hdop', float),
        ('msl_altitude', float),
        ('__units', str),
        ('geoidal_separation', float),
        ('__units', str),
        ('diff_corr_age', float),
    ]

    time: str | None = None
    """UTC time in hhmmss.sss format."""
    position_fix_indicator: PositionFixIndicator | None = None
    """Indicates the status of the position fix."""
    satelites_used: int | None = None
    """Number of satellites used in the fix. Ranges from 0 to 14"""
    hdop: float | None = None
    """Horizontal dilution of precision."""
    msl_altitude: float | None = None
    """Antenna altitude above/below mean sea level"""
    geoidal_separation: float | None = None
    """Geoidal separation in meters"""
    diff_corr_age: float | None = None
    """Age of differential corrections in seconds. ``None`` when DGPS is
    not used.
    """


@dataclass
class GPRMC(GPLocationDataSentence):
    """Store field values that can be outputted by the GPS for $GPRMC
    update messages by the PA1616S module: Time, date, position, course
    and speed data; recommended Minimum Navigation Information. See
    table 8 on datasheet.
    """

    class Status(StrEnum):
        """Status data transmitted by PA1616S in RMC mode. See table 8
        on datasheet.
        """

        VALID = 'A'
        """Data is valid"""
        INVALID = 'V'
        """Data is invalid"""

    MESSAGE_ID: ClassVar[str] = '$GPGGA'
    """The NMEA message ID for the GGA update message."""

    _STATIC_FIELD_SCHEMA: ClassVar[list[tuple[str, type]]] = [
        ('time', str),
        ('status', Status),
        ('_latitude', str),
        ('_NS_indicator', str),
        ('_longitude', str),
        ('_EW_indicator', str),
        ('speed_over_ground', float),
        ('course_over_ground', float),
        ('date', str),
        ('magnetic_variation', float),
        ('gp_mode', GPMode),
    ]

    time: str | None = None
    """UTC time in hhmmss.sss format."""
    status: Status | None = None
    """Status of the data. Either VALID or INVALID"""
    speed_over_ground: float | None = None
    """Speed over ground in knots"""
    course_over_ground: float | None = None
    """Course over ground in degrees"""
    date: str | None = None
    """UTC date in ddmmyy format"""
    magnetic_variation: float | None = None
    """Magnetic variation in degrees"""
    gp_mode: GPMode | None = None
    """Mode of operation"""


@dataclass
class GPVTG(GPOutputSentence):
    """Store field values that can be outputted by the GPS for $GPVTG
    update messages by the PA1616S module: course and speed information
    relative to the ground. See Table 9 on datasheet.
    """

    MESSAGE_ID: ClassVar[str] = "$GPVTG"
    """The NMEA message ID for the VTG update message."""

    _STATIC_FIELD_SCHEMA: ClassVar[list[tuple[str, type]]] = [
        ('true_course', float),
        ('__true_course_reference', str),
        ('magnetic_course', float),
        ('__magnetic_course_reference', str),
        ('speed_over_ground_knots', float),
        ('__units', str),
        ('speed_over_ground_kph', float),
        ('__units', str),
        ('gp_mode', GPMode),
    ]

    true_course: float | None = None
    """True course over ground in degrees"""
    magnetic_course: float | None = None
    """Magnetic course over ground in degrees"""
    speed_over_ground_knots: float | None = None
    """Speed over ground in knots"""
    speed_over_ground_kph: float | None = None
    """Speed over ground in kilometers per hour"""
    gp_mode: GPMode | None = None
    """Mode of operation"""


class GPOutputSentenceOptions(tuple[type[GPOutputSentence], int], Enum):
    """Types of update data packets to be outputted by the GPS PA1616S
    module. See Table 1 on datasheet.
    """

    RMC = GPRMC, 1
    """Time, date, position, course and speed data. Recommended Minimum
    Navigation Information.
    """
    VTG = GPVTG, 2
    """Course and speed information relative to the ground."""
    GGA = GPGGA, 3
    """Time, position and fix type data."""


@dataclass
class PA1616S:
    """A python driver for the CDTop PA1616S which utilizes the
    MediaTek GPS module MT3339 with a Serial UART Interface.
    """

    BAUD_RATE: ClassVar[int] = 9600
    """The supported baud rate for serial UART communication."""
    uart_interface: Serial
    """The serial UART interface for communication with the PA1616S."""
    _update_rate: int = 1000
    _enabled_update_modes: list[GPOutputSentenceOptions] = field(
        default_factory=lambda: [
            GPOutputSentenceOptions.GGA,
            GPOutputSentenceOptions.RMC,
        ],
    )
    _message_id_to_outputsentence_type: dict[str, type[GPOutputSentence]] = (
        field(default_factory=dict)
    )

    def __post_init__(self) -> None:
        if self.uart_interface.baudrate != self.BAUD_RATE:
            raise ValueError(
                (
                    f'Invalid baud rate. Expected {self.BAUD_RATE} but'
                    f' received {self.uart_interface.baudrate}'
                ),
            )

        self._send_uart_command(f'PMTK220,{self.update_rate}'.encode('ascii'))
        self._send_update_modes_msg()
        self._message_id_to_outputsentence_type = {
            output_option.value[0].MESSAGE_ID: output_option.value[0]
            for output_option in self._enabled_update_modes
        }

    @property
    def enabled_update_modes(self) -> list[GPOutputSentenceOptions]:
        """The type of update data packet outputted by the GPS module,
        in the order that they are outputted when receiving an update.
        """
        return self._enabled_update_modes

    @enabled_update_modes.setter
    def enabled_update_modes(
            self,
            modes: list[GPOutputSentenceOptions],
    ) -> None:
        """Set the type of update data packets outputted by the GPS
        module, in the order that they are outputted when receiving an
        update.
        """
        self._enabled_update_modes = modes
        self._send_update_modes_msg()

        self._message_id_to_outputsentence_type = {
            output_option.value[0].MESSAGE_ID: output_option.value[0]
            for output_option in self._enabled_update_modes
        }

    @property
    def update_rate(self) -> int:
        """The rate at which the GPS module sends update packets in
        milliseconds.
        """
        return self._update_rate

    @update_rate.setter
    def update_rate(self, rate: int) -> None:
        """Set the rate at which the GPS module sends update packets in
        milliseconds. See page 8-9 on PMTK datasheet.
        """
        self._update_rate = rate
        self._send_uart_command(f'PMTK220,{self.update_rate}'.encode('ascii'))

    def get_latest_update_packets(self) -> list[GPOutputSentence]:
        """Gets the latest set of update packets from the GPS module as
        :class:`GPOutputSentence` objects in the order stated in the
        enabled update modes.

        :return: A list of :class:`GPOutputSentence` instances in the
        order stated in the enabled update modes.
        """
        outputted_gp_sentences: list[GPOutputSentence | None] = [
            None for _ in self.enabled_update_modes
        ]
        received_uart_message = self.receive_next_uart_msg()

        while received_uart_message:
            message_id = received_uart_message[0:6]

            if message_id not in self._message_id_to_outputsentence_type:
                continue

            gp_sentence_obj = (
                self._message_id_to_outputsentence_type[message_id]
                .from_nmea_sentence(received_uart_message)
            )

            if gp_sentence_obj:
                index = next(
                    i
                    for i, (t, _) in enumerate(self.enabled_update_modes)
                    if t == self._message_id_to_outputsentence_type[message_id]
                )
                outputted_gp_sentences[index] = gp_sentence_obj

            received_uart_message = self.receive_next_uart_msg()

        return cast(list[GPOutputSentence], outputted_gp_sentences)

    def receive_next_uart_msg(self) -> str | None:
        """Reads the next NMEA sentence from the UART interface. Returns
        ``None`` if no message is available.

        :return: (Optional) The NMEA sentence string read from the UART
        interface.
        """
        if not self.uart_interface.poll():
            return None

        line = bytearray()

        while True:
            byte = self.uart_interface.read(1)
            if byte == b'\n':
                break
            line += byte

        return line.decode('ascii')

    def _send_update_modes_msg(self) -> None:
        """See page 12 on PMTK datasheet"""
        set_mode_data_list = [0] * 18
        for mode in self._enabled_update_modes:
            set_mode_data_list[mode.value[1]] = 1

        sub_message = ','.join(map(str, set_mode_data_list))
        full_set_mode_msg = f'PMTK314,{sub_message}'

        self._send_uart_command(full_set_mode_msg.encode('ascii'))

    def _send_uart_command(self, command: bytes) -> None:
        self.uart_interface.write(b'$')
        self.uart_interface.write(command)
        checksum = calculate_checksum(command.decode())
        self.uart_interface.write(f'*{checksum}\r\n'.encode())

from dataclasses import dataclass, field
from math import floor
from time import sleep
from typing import ClassVar
from warnings import warn

from freetype import Face  # type: ignore[import-untyped]
from periphery import GPIO, SPI


@dataclass
class NHDC12864A1ZFSWFBWHTT:
    """A Python driver for Newhaven Display Intl
    NHD-C12864A1Z-FSW-FBW-HTT COG (Chip-On-Glass) Liquid Crystal Display
    Module
    """

    WIDTH: ClassVar[int] = 128
    """The number of pixels by width."""
    HEIGHT: ClassVar[int] = 64
    """The number of pixels by height."""
    BASE_PAGE: ClassVar[int] = 0xB0
    """The address of the first page (of 8)."""
    DISPLAY_START_ADDRESS: ClassVar[int] = 0x40
    """The address of the display."""
    DISPLAY_OFF: ClassVar[int] = 0xAE
    """The command to turn the display off."""
    DISPLAY_ON: ClassVar[int] = 0xAF
    """The command to turn the display on."""
    TURN_POINTS_ON: ClassVar[int] = 0xA5
    """The command to confirm the writes on the display."""
    REVERT_NORMAL: ClassVar[int] = 0xA4
    """The command to show the result on the display."""

    SPI_MODE: ClassVar[int] = 0b11
    """The supported spi modes."""
    MIN_SPI_MAX_SPEED: ClassVar[float] = 5e4
    """The supported minimum spi maximum speed."""
    MAX_SPI_MAX_SPEED: ClassVar[float] = 30e6
    """The supported maximum spi maximum speed."""
    SPI_BIT_ORDER: ClassVar[str] = 'msb'
    """The supported spi bit order."""
    A0_PIN_DIRECTION: ClassVar[str] = 'out'
    """The direction of the a0 pin."""
    RESET_PIN_DIRECTION: ClassVar[str] = 'out'
    """The direction of the reset pin."""
    A0_PIN_INVERTED: ClassVar[bool] = False
    """The inverted status of A0 pin."""
    RESET_PIN_INVERTED: ClassVar[bool] = True
    """The inverted status of reset pin."""
    spi: SPI
    """The SPI for the display device."""
    a0_pin: GPIO
    """The mode select pin for the display device."""
    reset_pin: GPIO
    """The reset pin (active low) for the display device."""
    _framebuffer: list[int] = field(init=False)
    _face: Face | None = field(init=False)
    _font_width: int = field(init=False)
    _font_height: int = field(init=False)

    def __post_init__(self) -> None:
        if self.spi.mode != self.SPI_MODE:
            raise ValueError('unsupported spi mode')
        elif not (
                self.MIN_SPI_MAX_SPEED
                <= self.spi.max_speed
                <= self.MAX_SPI_MAX_SPEED
        ):
            raise ValueError('unsupported spi maximum speed')
        elif self.spi.bit_order != self.SPI_BIT_ORDER:
            raise ValueError('unsupported spi bit order')
        elif (
                self.a0_pin.direction != self.A0_PIN_DIRECTION
                or self.reset_pin.direction != self.RESET_PIN_DIRECTION
        ):
            raise ValueError('a0 and reset pin must be set to out')
        elif (
                self.a0_pin.inverted != self.A0_PIN_INVERTED
                or self.reset_pin.inverted != self.RESET_PIN_INVERTED
        ):
            raise ValueError('a0 must be active high and reset active low')

        if self.spi.extra_flags:
            warn(f'unknown spi extra flags {self.spi.extra_flags}')

        self._framebuffer = [0x0 for i in range(64 * 16)]
        self._face = None
        self._font_width = -1
        self._font_height = -1

        self._configure()

    def _configure(self) -> None:
        self.reset()
        self.a0_pin.write(False)
        self.spi.transfer([0xA0])  # ADC select.
        self.spi.transfer([self.DISPLAY_OFF])  # Display OFF.
        self.spi.transfer([0xC8])  # COM direction scan.
        self.spi.transfer([0xA2])  # LCD bias set.
        self.spi.transfer([0x2F])  # Power Control set.
        self.spi.transfer([0x26])  # Resistor Ratio Set.
        self.spi.transfer([0x81])  # Electronic Volume Command (set contrast).
        self.spi.transfer([0x11])  # Electronic Volume value (contrast value).
        self.spi.transfer([self.DISPLAY_ON])  # Display ON

    def reset(self) -> None:
        """Resets everything in the display.

        :return: ``None``.
        """
        self.reset_pin.write(True)
        sleep(0.1)
        self.reset_pin.write(False)

    def clear_screen(self, display: bool = True) -> None:
        """Clears the framebuffer and the display.

        :return: ``None``.
        """
        for i in range(len(self._framebuffer)):
            self._framebuffer[i] = 0x00

        if display:
            self.display()

    def display(self) -> None:
        """Writes what is in the local framebuffer to the display
        memory.

        :return: ``None``.
        """
        index = 0
        # Write LCD pixel data
        page = self.BASE_PAGE
        self.a0_pin.write(False)
        self.spi.transfer([self.DISPLAY_START_ADDRESS])

        for i in range(8):
            self.a0_pin.write(False)
            self.spi.transfer([page])
            self.spi.transfer([0x10])
            self.spi.transfer([0x00])
            self.a0_pin.write(True)

            for j in range(self.WIDTH):
                self.spi.transfer([self._framebuffer[index]])
                index += 1

            page += 1

        self.a0_pin.write(False)

    def framebuffer_offset(self, x: int, y: int) -> int:
        """Returns the flattened index in the framebuffer given an ``x``
        and ``y`` coordinate.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: The framebuffer offset.
        """
        return x + 128 * floor(y / 8)

    def page_offset(self, x: int, y: int) -> int:
        """Returns the page ``(1-8)`` given a coordinate on the display.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: The page offset.
        """
        return floor(y / 8)

    def write_pixel(self, x: int, y: int) -> None:
        """Turn on pixel at ``(x, y)`` in the framebuffer. This is does
        not immediately update the display.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: ``None``.
        """
        i = self.framebuffer_offset(x, y)
        self._framebuffer[i] = self._framebuffer[i] | (1 << (y % 8))

    def write_pixel_immediate(self, x: int, y: int) -> None:
        """Write to framebuffer and update display.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: ``None``.
        """
        i = self.framebuffer_offset(x, y)
        page = self.BASE_PAGE + self.page_offset(x, y)
        self.write_pixel(x, y)

        self.a0_pin.write(False)
        self.spi.transfer([page])
        self.spi.transfer([0x10])
        self.spi.transfer([0x00])
        self.a0_pin.write(True)
        self.spi.transfer([self._framebuffer[i]])

    def clear_pixel(self, x: int, y: int) -> None:
        """Turn off pixel at ``(x, y)`` in the framebuffer.

        This is does not immediately update the display.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: ``None``.
        """
        i = self.framebuffer_offset(x, y)
        self._framebuffer[i] = self._framebuffer[i] & ~(1 << (y % 8))

    def clear_pixel_immediate(self, x: int, y: int) -> None:
        """Write to framebuffer and update display.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: ``None``.
        """
        i = self.framebuffer_offset(x, y)
        page = self.BASE_PAGE + self.page_offset(x, y)
        self.clear_pixel(x, y)

        self.a0_pin.write(False)
        self.spi.transfer([page])
        self.spi.transfer([0x10])
        self.spi.transfer([0x00])
        self.a0_pin.write(True)
        self.spi.transfer([self._framebuffer[i]])

    def draw_fill_rect(self, x: int, y: int, width: int, height: int) -> None:
        """Draw a filled rectangle.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :param width: The width.
        :param height: The height.
        :return: ``None``
        """
        if (
                not self.pixel_in_bounds(x, y)
                or not self.pixel_in_bounds(x + width - 1, y + height - 1)
        ):
            return

        for row in range(height):
            for col in range(width):
                self.write_pixel(x + col, y + row)

    def draw_rect(self, x: int, y: int, width: int, height: int) -> None:
        """Draw a hollow rectangle.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :param width: The width.
        :param height: The height.
        :return: ``None``
        """
        if (
                not self.pixel_in_bounds(x, y)
                or not self.pixel_in_bounds(x + width - 1, y + height - 1)
        ):
            return

        for row in range(height):
            self.write_pixel(x, y + row)
            self.write_pixel(x + width - 1, y + row)

        for col in range(width):
            self.write_pixel(x + col, y)
            self.write_pixel(x + col, y + height - 1)

    def set_font(self, filename: str) -> None:
        """Set the font for drawing letters.

        :param filename: The ``.ttf`` file to set.
        :return: ``None``.
        """
        self._face = Face(filename)

    def pixel_in_bounds(self, x: int, y: int) -> bool:
        """Checks if the x and y coordinate is
        within the bounds of the display resolution.
        """
        return x >= 0 and x <= self.WIDTH and y >= 0 and y <= self.HEIGHT

    def set_size(self, width: int, height: int) -> None:
        """Set the size of the letters.

        :param width: The width.
        :param height: The height.
        :return: ``None``.
        """
        if self._face is None:
            return

        # freetype uses 26.6 scaling, so the first 6 lsb are for decimals.
        self._face.set_char_size(width << 6, height << 6)
        self._font_width = width
        self._font_height = height

    def draw_letter(self, letter: str, x: int, y: int) -> None:
        """Draw the letter at position ``(x, y)``.

        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: ``None``.
        """
        if (
                self._face is None
                or (
                    not self.pixel_in_bounds(
                        x + self._font_width,
                        y + self._font_height,
                    )
                )
        ):
            return

        self._face.load_char(letter)
        bitmap = self._face.glyph.bitmap

        for row in range(bitmap.rows):
            for col in range(bitmap.width):
                if x + col >= self.WIDTH or y + row >= self.HEIGHT:
                    continue

                if bitmap.buffer[row * bitmap.pitch + col]:
                    self.write_pixel(x + col, y + row)
                else:
                    self.clear_pixel(x + col, y + row)

    def draw_word(self, word: str, x: int, y: int) -> None:
        """Draws the word while wrapping if offscreen.

        :param word: The word.
        :param x: The ``x`` coordinate.
        :param y: The ``y`` coordinate.
        :return: ``None``
        """
        if (
                self._face is None
                or (
                    not self.pixel_in_bounds(
                        x + self._font_width,
                        y + self._font_height,
                    )
                )
        ):
            return

        x_off = x
        y_off = y

        for letter in word:
            if y_off + self._font_height >= self.HEIGHT:
                break

            if x_off + self._font_width >= self.WIDTH:
                x_off = x
                y_off += self._font_height

            self.draw_letter(letter, x_off, y_off)
            x_off += self._font_width

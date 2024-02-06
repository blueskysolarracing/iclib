from dataclasses import dataclass
from typing import ClassVar
from math import floor
from warnings import warn
import time

from periphery import SPI, GPIO
import freetype


@dataclass
class NHDC12864A1ZFSWFBWHTT:
    """A Python driver for Newhaven Display Intl
    NHD-C12864A1Z-FSW-FBW-HTT COG (Chip-On-Glass) Liquid Crystal Display
    Module

    TODO: Benchmark time.sleep delays between hardware transfers and delete
          the delay if it is uneeded.
    """

    SPI_MODES: ClassVar[tuple[int, int]] = 0b00, 0b11
    """The supported spi modes."""
    MIN_SPI_MAX_SPEED: ClassVar[float] = 5e4
    """The supported minimum spi maximum speed."""
    MAX_SPI_MAX_SPEED: ClassVar[float] = 30e6
    """The supported maximum spi maximum speed."""
    SPI_BIT_ORDER: ClassVar[str] = 'msb'
    """The supported spi bit order."""

    TIME_DELAY: ClassVar[float] = 0.01
    '''The time in seconds to delay between operations'''
    WIDTH: ClassVar[int] = 128
    '''The number of pixels by width.'''
    HEIGHT: ClassVar[int] = 64
    '''The number of pixels by height.'''
    BASE_PAGE: ClassVar[int] = 0xB0
    '''The address of the first page (of 8).'''
    DISPLAY_START_ADDRESS: ClassVar[int] = 0x40
    '''The address of the display.'''
    DISPLAY_OFF: ClassVar[int] = 0xAE
    '''The command to turn the display off.'''
    DISPLAY_ON: ClassVar[int] = 0xAF
    '''The command to turn the display on.'''
    TURN_POINTS_ON: ClassVar[int] = 0xA5
    '''The command to confirm the writes on the display.'''
    REVERT_NORMAL: ClassVar[int] = 0xA4
    '''The command to show the result on the display.'''

    spi: SPI
    '''The SPI for the display device.'''
    a0_pin: GPIO
    '''The mode select pin for the display device.'''
    reset_pin: GPIO
    '''The reset pin (active low) for the display device.'''

    def __post_init__(self) -> None:
        if self.spi.mode not in self.SPI_MODES:
            raise ValueError('unsupported spi mode')
        elif not (
                self.MIN_SPI_MAX_SPEED
                <= self.spi.max_speed
                <= self.MAX_SPI_MAX_SPEED
        ):
            raise ValueError('unsupported spi maximum speed')
        elif self.spi.bit_order != self.SPI_BIT_ORDER:
            raise ValueError('unsupported spi bit order')

        if self.spi.extra_flags:
            warn(f'unknown spi extra flags {self.spi.extra_flags}')

        self.framebuffer = [0x0 for i in range(64 * 16)]
        self.face = None
        self.font_width = -1
        self.font_height = -1

    def reset(self) -> None:
        '''Resets everything in the display.'''

        self.reset_pin.write(False)
        time.sleep(self.TIME_DELAY)
        self.reset_pin.write(True)

    def configure(self) -> None:
        '''Configures the diplay for normal operation.'''

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
        self.spi.transfer([self.DISPLAY_ON])  # Display ON.

    def clear_screen(self) -> None:
        '''Clears the framebuffer and the display.'''

        for i in range(len(self.framebuffer)):
            self.framebuffer[i] = 0x00
        self.display()

    def display(self):
        '''Writes what is in the local framebuffer to the display memory.'''

        index = 0
        # Write LCD pixel data
        page = self.BASE_PAGE
        self.spi.transfer([self.DISPLAY_OFF])
        self.spi.transfer([self.DISPLAY_START_ADDRESS])
        for i in range(8):
            self.spi.transfer([page])
            self.spi.transfer([0x10])
            self.spi.transfer([0x00])
            self.a0_pin.write(True)
            time.sleep(self.TIME_DELAY)
            for j in range(128):
                # write pixel data
                self.spi.transfer([self.framebuffer[index]])
                index += 1
            time.sleep(self.TIME_DELAY)
            self.a0_pin.write(False)
            page += 1
        self.spi.transfer([self.DISPLAY_ON])  # Turn on display.
        time.sleep(self.TIME_DELAY)
        self.spi.transfer([self.TURN_POINTS_ON])
        time.sleep(self.TIME_DELAY)
        self.spi.transfer([self.REVERT_NORMAL])

    def framebuffer_offset(self, x: int, y: int) -> int:
        return x + 128 * floor(y / 8)

    def page_offset(self, x: int, y: int) -> int:
        return floor(y / 8)

    def write_pixel(self, x: int, y: int) -> None:
        '''Turn on pixel at (x, y) in the framebuffer.
        This is does not immediately update the display.
        '''

        i = self.framebuffer_offset(x, y)
        self.framebuffer[i] = self.framebuffer[i] | (1 << (y % 8))

    def write_pixel_immediate(self, x: int, y: int) -> None:
        '''Write to framebuffer and update display.'''

        i = self.framebuffer_offset(x, y)
        page = self.BASE_PAGE + self.page_offset(x, y)
        self.write_pixel(x, y)

        self.spi.transfer([page])
        self.spi.transfer([0x10])
        self.spi.transfer([0x00])
        self.a0_pin.write(True)
        time.sleep(self.TIME_DELAY)
        self.spi.transfer([self.framebuffer[i]])
        time.sleep(self.TIME_DELAY)
        self.a0_pin.write(False)

    def clear_pixel(self, x: int, y: int) -> None:
        '''Turn off pixel at (x, y) in the framebuffer.
        This is does not immediately update the display.
        '''

        i = self.framebuffer_offset(x, y)
        self.framebuffer[i] = self.framebuffer[i] & ~(1 << (y % 8))

    def clear_pixel_immediate(self, x: int, y: int) -> None:
        '''Write to framebuffer and update display.'''

        i = self.framebuffer_offset(x, y)
        page = self.BASE_PAGE + self.page_offset(x, y)
        self.clear_pixel(x, y)

        self.spi.transfer([page])
        self.spi.transfer([0x10])
        self.spi.transfer([0x00])
        self.a0_pin.write(True)
        time.sleep(self.TIME_DELAY)
        self.spi.transfer([self.framebuffer[i]])
        time.sleep(self.TIME_DELAY)
        self.a0_pin.write(False)

    def draw_fill_rect(self, x: int, y: int, width: int, height: int) -> None:
        '''Draw a filled rectangle.'''

        if not self.pixel_in_bounds(x, y) or \
           not self.pixel_in_bounds(x + width - 1, y + height - 1):
            return

        for row in range(height):
            for col in range(width):
                self.write_pixel(x + col, y + row)

    def draw_rect(self, x: int, y: int, width: int, height: int):
        '''Draw an hollow rectangle.'''

        if not self.pixel_in_bounds(x, y) or \
           not self.pixel_in_bounds(x + width - 1, y + height - 1):
            return

        for row in range(height):
            self.write_pixel(x, y + row)
            self.write_pixel(x + width - 1, y + row)
        for col in range(width):
            self.write_pixel(x + col, y)
            self.write_pixel(x + col, y + height - 1)

    def set_font(self, filename: str) -> None:
        '''Set the font for drawing letters.

        :param filename: The ".ttf" file to set.
        '''

        self.face = freetype.Face(filename)

    def pixel_in_bounds(self, x: int, y: int) -> bool:
        return x >= 0 and x <= self.WIDTH and y >= 0 and y <= self.HEIGHT

    def set_size(self, width: int, height: int) -> None:
        '''Set the size of the letters.'''

        if self.face is None:
            return

        # freetype uses 26.6 scaling, so the first 6 lsb are for decimals.
        self.face.set_char_size(width << 6, height << 6)
        self.font_width = width
        self.font_height = height

    def draw_letter(self, letter: str, x: int, y: int) -> None:
        '''Draw (letter) at position (x, y).'''

        if self.face is None or not \
           self.pixel_in_bounds(x + self.font_width, y + self.font_height):
            return

        self.face.load_char(letter)
        bitmap = self.face.glyph.bitmap
        for row in range(bitmap.rows):
            for col in range(bitmap.width):
                if x + col >= self.WIDTH or y + row >= self.HEIGHT:
                    continue
                if bitmap.buffer[row * bitmap.pitch + col]:
                    self.write_pixel(x + col, y + row)
                else:
                    self.clear_pixel(x + col, y + row)

    def draw_word(self, word: str, x: int, y: int) -> None:
        '''Draws word while wrapping if offscreen.'''

        if self.face is None or not \
           self.pixel_in_bounds(x + self.font_width, y + self.font_height):
            return

        x_off = x
        y_off = y
        for letter in word:
            if y_off + self.font_height >= self.HEIGHT:
                return
            if x_off + self.font_width >= self.WIDTH:
                x_off = x
                y_off += self.font_height
            self.draw_letter(letter, x_off, y_off)
            x_off += self.font_width

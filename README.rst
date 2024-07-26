=====
ICLib
=====

ADC78H89 is a A collection of integrated circuit libraries in pure Python.

Features
--------

- High-level integrated circuit usage.
- Low-level integrated circuit usage.

Installation
------------

.. code-block:: bash

   pip install iclib

Usage
-----

Below shows a sample usage of ADC78H89.

.. code-block:: python

   from iclib.adc78h89 import ADC78H89
   from periphery import SPI

   spi = SPI('/dev/spidev0.0', 3, 1e6)
   adc78h89 = ADC78H89(spi)
   voltages = adc78h89.sample_all()

   print(voltages[ADC78H89.InputChannel.AIN1])
   print(voltages[ADC78H89.InputChannel.GROUND])

Below shows a sample usage of MCP4161.

.. code-block:: python

   from iclib.mcp4161 import MCP4161
   from periphery import SPI

   spi = SPI('/dev/spidev0.0', 3, 1e6)
   mcp4161 = MCP4161(spi)

   mcp4161.set_wiper_step(123, True)  # eeprom
   mcp4161.set_wiper_step(123)

Below shows a sample usage of SN74HCS137.

.. code-block:: python

   from time import sleep
   from unittest.mock import MagicMock

   from periphery import GPIO
   from iclib.sn78hcs137 import SN74HCS137
   
   latch_enable_gpio = GPIO('/dev/gpiochip0', 0, 'out', inverted=True)
   strobe_input_gpio = GPIO('/dev/gpiochip0', 1, 'out', inverted=True)
   address_select_0_gpio = GPIO('/dev/gpiochip0', 2, 'out', inverted=False)
   address_select_1_gpio = GPIO('/dev/gpiochip0', 3, 'out', inverted=False)
   address_select_2_gpio = GPIO('/dev/gpiochip0', 4, 'out', inverted=False)
   sn78hcs137 = SN74HCS137(
       latch_enable_gpio,
       MagicMock(),
       strobe_input_gpio,
       address_select_0_gpio,
       address_select_1_gpio,
       address_select_2_gpio,
   )

   sn78hcs137.select(SN74HCS137.Address.Y3)
   sleep(1)
   sn78hcs137.deselect()

Below shows a sample usage of NHD-C12864A1Z-FSW-FBW-HTT.

.. code-block:: python

   from time import sleep

   from periphery import GPIO, SPI
   from iclib.nhd_c12864a1z_fsw_fbw_htt import NHDC12864A1ZFSWFBWHTT 

   spi = SPI('/dev/spidev0.0', 3, 10e6)
   a0 = GPIO('/dev/gpiochip0', 8, 'out')
   not_reset = GPIO('/dev/gpiochip0', 9, 'out')
   display = NHDC12864A1ZFSWFBWHTT(spi, a0, not_reset)

   display.clear_screen()

   display.draw_rect(0, 0, 127, 63)

   display.set_font('dejavusans.ttf')
   display.set_size(8, 14)
   display.draw_word('Welcome to Blue Sky solar racing! 12345678910', 2, 2)
   display.set_size(16, 16)
   display.draw_word('@#$%*^', 1, int(driver.HEIGHT * 0.7))
   display.display()

   sleep(5)

   display.clear_screen()

    # Fill screen
    for row in range(display.HEIGHT)
        for col in range(display.WIDTH)
            display.write_pixel(col, row)

    display.display()

    # Create checkerboard pattern
    for row in range(display.HEIGHT)
        for col in range(display.WIDTH)
            if (row + col) % 2 == 1:  # Checker pattern
                display.clear_pixel(col, row)

Testing and Validation
----------------------

ICLib has extensive test coverage, passes mypy static type checking with strict
parameter, and has been validated through extensive use in real-life scenarios.

Contributing
------------

Contributions are welcome! Please read our Contributing Guide for more
information.

License
-------

ICLib is distributed under the MIT license.

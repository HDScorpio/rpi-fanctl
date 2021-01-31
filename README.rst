**rpi-fanctl** is a simple script for fan control of Raspberry Pi through GPIO.

Installation
------------

::

    pip install rpi-fanctl

Usage
-----

::

    $ rpi-fanctl --help
    usage: rpi-fanctl [-h] [--debug] [--dry-run] [--pin PIN] [--high HIGH] [--low LOW] [--time TIME]
                      [--install-systemd-service] [--log-datetime]

    Raspberry Pi fan control script.

    optional arguments:
      -h, --help            show this help message and exit
      --debug               print debug messages to stdout
      --dry-run             run without pin control
      --pin PIN             GPIO pin number to control fan, default 14
      --high HIGH           fan start temperature, default 70°C
      --low LOW             fan stop temperature, default 50°C
      --time TIME           temperature polling time, default 10 second
      --install-systemd-service
                            install systemd service rpi-fanctl.service
      --log-datetime        print date and time


Systemd service
---------------

Use argument ``--install-systemd-service`` to make systemd service.
If running under *root* than service will be made at
``/etc/systemd/system/rpi-fanctl.service``,
else at ``~/.config/systemd/user/rpi-fanctl.service``.


Links
-----

* `Fan schema <http://codius.ru/articles/Raspberry_Pi_3_GPIO_часть_3>`_

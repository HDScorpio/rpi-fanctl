#!/usr/bin/python2
"""
Raspberry Pi fan control script

Author: Andrey Ulagashev (ulagashev.andrey@gmail.com)
"""

import argparse
from getpass import getuser
import logging
import os
import signal
import sys
from threading import Event

gpio_import_error = None
try:
    from RPi import GPIO
except (ImportError, RuntimeError) as e:
    GPIO = None
    gpio_import_error = e


PIN_CONTROL = 14
FAN_STATE = False
TEMP_LOW = 50.0
TEMP_HIGH = 70.0
POLL_TIME = 10
DRY_RUN = False

_TEMP_SYS_PATH = '/sys/devices/virtual/thermal/thermal_zone0/temp'
_TEMP_SYS_FD = None
_EVENT_EXIT = Event()

logger = logging.getLogger()


def parse_arguments():
    global PIN_CONTROL, TEMP_HIGH, TEMP_LOW, POLL_TIME, DRY_RUN

    parser = argparse.ArgumentParser(
        prog='rpi-fanctl',
        description='Raspberry Pi fan control script.'
    )
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='print debug messages to stdout')
    parser.add_argument(
        '--dry-run', action='store_true', default=False,
        help='run without pin control')
    parser.add_argument(
        '--pin', type=int, default=PIN_CONTROL,
        help='GPIO pin number to control fan, default %d' % PIN_CONTROL)
    parser.add_argument(
        '--high', type=float, default=TEMP_HIGH,
        help='fan start temperature, default %d\u00B0C' % TEMP_HIGH)
    parser.add_argument(
        '--low', type=float, default=TEMP_LOW,
        help='fan stop temperature, default %d\u00B0C' % TEMP_LOW)
    parser.add_argument(
        '--time', type=int, default=POLL_TIME,
        help='temperature polling time, default %d second' % POLL_TIME)
    parser.add_argument(
        '--install-systemd-service', action='store_true', default=False,
        help='install systemd service rpi-fanctl.service')
    parser.add_argument(
        '--log-datetime', action='store_true', default=False,
        help='print date and time')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.log_datetime:
        fmt = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s',
                                '%Y-%m-%d %H:%M:%S')
    else:
        fmt = logging.Formatter('%(levelname)s: %(message)s')
    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    if args.install_systemd_service:
        systemd_service_setup(args)

    PIN_CONTROL = args.pin
    TEMP_HIGH = args.high
    TEMP_LOW = args.low
    POLL_TIME = args.time
    DRY_RUN = args.dry_run


def signal_handler(signal_num, _):
    logger.warning('Interrupted by signal %d, shutting down', signal_num)
    _EVENT_EXIT.set()


def setup():
    global _TEMP_SYS_FD

    logger.info('Setup: pin=%d, high=%.2f, low=%.2f, time=%d, dry_run=%s',
                PIN_CONTROL, TEMP_HIGH, TEMP_LOW, POLL_TIME, DRY_RUN)

    if not DRY_RUN:
        if GPIO is None:
            logger.error('Failed to import RPi.GPIO: %s',
                         gpio_import_error)
            sys.exit(1)
        # Pin numbering mode - BCM
        GPIO.setmode(GPIO.BCM)
        # Setup pin to OUT mode
        GPIO.setup(PIN_CONTROL, GPIO.OUT, initial=0)

    try:
        _TEMP_SYS_FD = open(_TEMP_SYS_PATH, mode='r')
    except FileNotFoundError:
        logger.error('Failed to open "%s" file: need newer firmware',
                     _TEMP_SYS_PATH)
        sys.exit(1)

    signal.signal(signal.SIGTERM, signal_handler)


def get_temperature():
    temp_raw = _TEMP_SYS_FD.read()  # 52616
    _TEMP_SYS_FD.seek(0)

    return float('%s.%s' % (temp_raw[:2], temp_raw[2:]))


def cleanup():
    logger.info('Cleanup: fan will stop')
    if _TEMP_SYS_FD:
        _TEMP_SYS_FD.close()
    if not DRY_RUN:
        GPIO.cleanup()

    sys.exit(0)


def fan_switch():
    global FAN_STATE

    FAN_STATE = not FAN_STATE
    if not DRY_RUN:
        GPIO.output(PIN_CONTROL, FAN_STATE)


def poll_loop():
    while not _EVENT_EXIT.is_set():
        temp = get_temperature()

        if FAN_STATE and temp <= TEMP_LOW:
            # fan is on and temp is low - stop fan
            logger.info("fan off, temperature '%.2f'", temp)
            fan_switch()
        elif not FAN_STATE and temp >= TEMP_HIGH:
            # fan is off and temp is high - start fan
            logger.info("fan on, temperature '%.2f'", temp)
            fan_switch()

        logger.debug("temperature '%.2f', fan status '%s'",
                     temp, 'on' if FAN_STATE else 'off')

        _EVENT_EXIT.wait(POLL_TIME)


def systemd_service_setup(args):
    template = '''[Unit]
Description=Raspberry Pi fan control service

[Service]
Type=simple{user:s}
Environment=PYTHONUNBUFFERED=1
ExecStart={script:s} --pin {pin:d} --high {high:.2f} --low {low:.2f} --time {time:d}
ExecStop=/bin/kill -s SIGTERM $MAINPID

[Install]
WantedBy=default.target
'''

    user_path = '~/.config/systemd/user/rpi-fanctl.service'
    system_path = '/etc/systemd/system/rpi-fanctl.service'

    user = getuser()
    if user == 'root':
        user = '\nUser=nobody'
        service_path = system_path
    else:
        user = ''
        service_path = os.path.expanduser(user_path)

    service_dir = os.path.dirname(service_path)
    os.makedirs(service_dir, exist_ok=True)

    with open(service_path, mode='w') as f:
        f.write(template.format(
            user=user,
            script=sys.argv[0],
            pin=args.pin,
            high=args.high,
            low=args.low,
            time=args.time
        ))

    logger.info("Systemd service successfully made at '%s'", service_path)
    sys.exit(0)


def main():
    parse_arguments()
    setup()

    try:
        poll_loop()
    except KeyboardInterrupt:
        logger.warning('Interrupted by Ctrl+C, shutting down')
    except Exception as err:
        logger.exception('Unknown exception occurred: %s', err)
    finally:
        cleanup()


if __name__ == '__main__':
    main()

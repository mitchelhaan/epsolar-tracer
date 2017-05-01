#!/usr/bin/env python3

from pyepsolartracer.client import EPsolarTracerClient
import datetime
import time
import logging

# configure the client logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

current_stats_file = "/opt/solar_current_stats.csv"
daily_stats_file = "/opt/solar_daily_stats.csv"

is_daytime = False
loop_interval_sec = 5 * 60.0


def status_loop():
    client = EPsolarTracerClient()

    while True:
        loop_start = time.monotonic()

        was_daytime = is_daytime
        update_daytime_state(client)

        if is_daytime:
            get_current_stats(client)

        # Collect daily stats on the day -> night transition
        if was_daytime and not is_daytime:
            get_day_stats(client)

        loop_duration = time.monotonic() - loop_start

        if loop_duration < loop_interval_sec:
            remaining = loop_interval_sec - loop_duration
            log.debug("Finished loop with {} seconds remaining", remaining)
            time.sleep(remaining)


def update_daytime_state(client):
    global is_daytime

    client.connect()
    day_night = client.read_input("Day/Night")

    if day_night is not None:
        is_daytime = int(day_night) == 0
    else:
        day_voltage = float(client.read_input("Day Time Threshold Volt.(DTTV)"))
        night_voltage = float(client.read_input("Night Time Threshold Volt.(NTTV)"))
        current_voltage = float(client.read_input("Charging equipment input voltage"))

        # There should be a gap between day/night voltage to allow hysteresis
        if current_voltage <= night_voltage:
            is_daytime = False
        if current_voltage >= day_voltage:
            is_daytime = True

    client.close()


def get_current_stats(client):
    client.connect()
    pv_v = float(client.read_input("Charging equipment input voltage"))
    pv_a = float(client.read_input("Charging equipment input current"))
    bc_v = float(client.read_input("Charging equipment output voltage"))
    bc_a = float(client.read_input("Charging equipment output current"))
    b_temp = float(client.read_input("Battery Temp."))
    a_temp = float(client.read_input("Ambient Temp."))
    client.close()

    data = [datetime.datetime.now(), pv_v, pv_a, (pv_v * pv_a), bc_v, bc_a, (bc_v * bc_a), b_temp, a_temp]
    with open(current_stats_file, 'a') as f:
        f.write(",".join(map(lambda d: str(d), data)) + "\n")


def get_day_stats(client):
    client.connect()
    gen_today = float(client.read_input("Generated energy today"))
    gen_total = float(client.read_input("Total generated energy"))
    client.close()

    data = [datetime.datetime.now(), gen_today, gen_total]

    with open(daily_stats_file, 'a') as f:
        f.write(",".join(map(lambda d: str(d), data)) + "\n")


if __name__ == "__main__":
    status_loop()

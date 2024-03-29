import re
import os
import subprocess
from iriscasttools.utils import check_ipmi_conn, ipmi_query_power, to_csv, run_cmd


def get_iriscast_stats(poll_period_seconds=300, csv=False, include_header=False):
    """ get stats for iriscast """
    stats = {}

    # get power info
    power_stats = get_all_power_stats()
    if power_stats['current_power']:
        power_stats['watt_hours'] = round(
            int(power_stats['current_power']) * (poll_period_seconds/3600), 3
        )
    else:
        power_stats['watt_hours'] = ''

    stats.update(power_stats)

    # get os load info
    stats.update(get_os_load())

    # get ram info
    stats.update(get_ram_usage())

    if csv:
        return to_csv(stats, include_header)
    return stats


def get_current_power(csv=False):
    """ get current power info from ipmitool """
    if not check_ipmi_conn():
        return None
    res = ipmi_query_power()

    power_stats = {
        "current_power": ''
    }

    for line in res.splitlines():
        line_str = line.split(b":")
        stat = line_str[0].decode().strip().lower().replace(" ", "_")
        if stat == "current_power":
            power_str = "".join([l.decode() for l in line_str[1:]]).strip()
            power_stats[stat] = re.search("[0-9]+", power_str).group(0)

    if csv:
        return to_csv(power_stats)
    return power_stats


def get_all_power_stats(csv=False):
    """ get all power info from ipmitool """
    if not check_ipmi_conn():
        return None
    res = ipmi_query_power()

    power_stats = {
        "current_power": '',
        "min": '',
        "max": '',
        "average": '',
        "sampling_period": ''
    }
    if res:
        for line in res.splitlines():
            line_str = line.split(b":")
            stat = line_str[0].decode().strip().lower().replace(" ", "_")
            val_str = ":".join([l.decode() for l in line_str[1:]]).strip()

            key, val = {
                "current_power": lambda a: ("current_power", re.search("[0-9]+", a).group(0)),
                "minimum_power_over_sampling_duration": lambda a: ("min", re.search("[0-9]+", a).group(0)),
                "maximum_power_over_sampling_duration": lambda a: ("max", re.search("[0-9]+", a).group(0)),
                "average_power_over_sampling_duration": lambda a: ("average", re.search("[0-9]+", a).group(0)),
                "statistics_reporting_time_period": lambda a: ("sampling_period", re.search("[0-9]+", a).group(0))
            }.get(stat, lambda a: (None, None))(val_str)
            if key:
                power_stats[key] = val

    if csv:
        return to_csv(power_stats)
    return power_stats



def get_os_load(csv=False):
    """ get os load average from os """
    try:
        loads = os.getloadavg()
        stat = {
            "os_load_1": loads[0],
            "os_load_5": loads[1],
            "os_load_15": loads[2]
        }
    except OSError:
        stat = {
            "os_load_1": '',
            "os_load_5": '',
            "os_load_15": ''
        }

    if csv:
        return to_csv(stat)
    return stat


def get_ram_usage(csv=False):
    """ get ram usage """
    max_ram = int(run_cmd(
        "free -k | sed -n '2p' | awk '{print $2}'",
    ))

    used_ram = int(run_cmd(
        "free -k | sed -n '2p' | awk '{print $3}'"
    ))
    stat = {"ram_usage_percentage": ''}
    if max_ram and used_ram:
        stat["ram_usage_percentage"] = round(
            (used_ram/max_ram)*100, 3
        )

    if csv:
        return to_csv(stat)
    return stat

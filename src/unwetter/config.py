#!/user/bin/env python3.6

import yaml


COLORS = {
    "SEVERITIES": {
        "Minor": "#ffcc00a0",
        "Moderate": "#ff6600a0",
        "Severe": "#ff0000a0",
        "Extreme": "#b00087a3",
        "Disabled": "#999999e0",
    },
}


def severity_key(event):
    mapped = {
        "Minor": 0,
        "Moderate": 1,
        "Severe": 2,
        "Extreme": 3,
    }

    return mapped.get(event["severity"], 100)


with open("config/config.yml", "r") as fp:
    CONFIG = yaml.safe_load(fp.read())

SEVERITY_FILTER = CONFIG["SEVERITY_FILTER"]
STATES_FILTER = CONFIG["STATES_FILTER"]
URGENCY_FILTER = CONFIG["URGENCY_FILTER"]


def filter_event(event):
    return (
        event["severity"] in SEVERITY_FILTER
        and event["urgency"] in URGENCY_FILTER
        and len(set(event["states"]) - set(STATES_FILTER)) < len(event["states"])
    )

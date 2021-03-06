#!/user/bin/env python3.6
import os

from slack_sdk.web import WebClient

from . import db, generate
from .generate import helpers, urls
from .config import COLORS, SEVERITY_FILTER, STATES_FILTER


# Set up Slack client
# Based on https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
CHANNEL = os.environ.get("SLACK_CHANNEL")
CLIENT = WebClient(SLACK_TOKEN)


def post_event(event):

    change_title = ""
    the_changes = ""

    if event["msg_type"] != "Alert" and event["special_type"] != "UpdateAlert":

        old_events = [
            event for event in db.by_ids(event["references"]) if event.get("published")
        ]

        if len(old_events) == 1:
            old_event = old_events[0]
            old_time = generate.local_time(old_event["sent"]).strftime(
                "%d.%m.%Y, %H:%M:%S Uhr"
            )

            if event["msg_type"] == "Cancel" or event["response_type"] == "AllClear":
                change_title = f"Aufhebung der Meldung von {old_time}\n"
                the_changes = ""
            elif (
                event["special_type"] == "Irrelevant"
                and event["severity"] not in SEVERITY_FILTER
            ):
                change_title = f"Herabstufung der Meldung von {old_time}\n"
                the_changes = "*Änderungen:*\n\n" + (
                    generate.changes(event, old_event) if old_event else "Unbekannt"
                )
            elif event["special_type"] == "Irrelevant" and not any(
                state in event["states"] for state in STATES_FILTER
            ):
                change_title = f"Änderung der Meldung von {old_time}\n"
                the_changes = (
                    f"Die Unwetterzelle befindet sich"
                    f' nicht mehr im Bundesland {", ".join(STATES_FILTER)}.\n\n'
                )
            else:
                change_title = f"Änderungen zur Meldung von {old_time}\n"
                the_changes = "*Änderungen:*\n\n" + (
                    generate.changes(event, old_event) if old_event else "Unbekannt"
                )
        else:
            old_times = [
                generate.local_time(old_event["sent"]).strftime(
                    "%d.%m.%Y, %H:%M:%S Uhr"
                )
                for old_event in old_events
            ]

            if event["msg_type"] == "Cancel" or event["response_type"] == "AllClear":
                change_title = f'Aufhebung der Meldungen von {", ".join(old_times)}\n'
                the_changes = ""
            elif event["special_type"] == "Irrelevant":
                change_title = (
                    f"Aufhebung der Meldungen von " f'{", ".join(old_times)}\n'
                )
                the_changes = (
                    "\n\n".join(
                        f"*Änderungen zu {old_time}*:\n{generate.changes(event, old_event)}"
                        for old_time, old_event in zip(old_times, old_events)
                    )
                    or ""
                )
            else:
                change_title = (
                    f"Zusammenführung und Aktualisierung zur Meldungen von "
                    f'{", ".join(old_times)}\n'
                )
                the_changes = (
                    "\n\n".join(
                        f"*Änderungen zu {old_time}*:\n{generate.changes(event, old_event)}"
                        for old_time, old_event in zip(old_times, old_events)
                    )
                    or ""
                )

    response = post_message(
        "",
        attachments=[
            {
                "fallback": generate.title(event),
                "color": COLORS["SEVERITIES"][event["severity"]],
                "title": generate.title(event),
                "text": f"{change_title}Gültig {generate.dates(event)}",
                "fields": [
                    {
                        "title": generate.severities[event["severity"]],
                        "value": generate.parameters(event),
                        "short": False,
                    },
                ],
                "callback_id": event["id"],
                "footer": "Details zur Meldung im Thread",
                "ts": int(event["sent"].timestamp()),
                "mrkdwn_in": [],
            }
        ],
    )

    thread_ts = response["ts"]

    instruction = (
        helpers.pad(f'_Verhaltenshinweise_: {event["instruction"]}')
        if event["instruction"]
        else ""
    )

    post_message(
        f"""
{the_changes}
*Details:*

_Regionale Zuordnung_: {generate.region_list(event)}
 Download Karte: {urls.events(event)}
{instruction}
{event['description']}
        """.strip(),
        mrkdwn=True,
        thread_ts=thread_ts,
    )


def post_message(message, *, private=False, channel=CHANNEL, **kwargs):
    """
    Send message with attachments to Slack on channel. Set 'private' to a user ID to send a message
    that only that user can see. Set 'channel' to a specific ID to send in a channel different from
    the default channel.
    """
    if not private:
        return CLIENT.chat_postMessage(
            channel=channel,
            text=message,
            **kwargs,
        )
    else:
        return CLIENT.chat_postEphemeral(
            channel=channel,
            user=private,
            text=message,
            **kwargs,
        )

#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""
from time import sleep
import datetime as dt

from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

from unwetter import db, slack, wina, sentry
from unwetter.config import filter_event
from unwetter.generate.helpers import BERLIN, local_now


sentry.init()
sched = BlockingScheduler(timezone=BERLIN)


@sched.scheduled_job("interval", minutes=1)
def update_db():
    """
    You should not do actual work in the scheduler.
    For now, we do it anyways.
    """
    print("Running update job")
    new_events = db.update()

    if new_events is None:
        return

    # Filter new_events by SEVERITY_FILTER, URGENCY_FILTER and STATES_FILTER
    filtered = []
    for event in new_events:
        if event["msg_type"] == "Cancel" and any(
            item["published"] for item in event["has_changes"]
        ):
            filtered.append(event)

        elif not filter_event(event):
            continue

        elif event["msg_type"] == "Alert":
            filtered.append(event)

        elif any(
            item["changed"] and item["published"] for item in event["has_changes"]
        ):
            filtered.append(event)

        elif event["special_type"] == "UpdateAlert":
            filtered.append(event)

        elif not any(
            item["changed"] and item["published"] for item in event["has_changes"]
        ):
            continue

        else:
            sentry.sentry_sdk.capture_message(f'Event was not filtered: {event["id"]}')

    if filtered:
        db.publish([event["id"] for event in filtered])

        wina.upload_ids([event["id"] for event in filtered])

        for event in filtered:
            print(f'Sending event {event["id"]} to Slack')
            slack.post_event(event)
            sleep(1)


# @sched.scheduled_job("interval", minutes=5)
def post_clear_warning():

    currently_events = db.current_events(all_severities=False)
    if currently_events:
        db.set_warn_events_memo(True)
        print("Active events: warn events memo ON")
    elif db.warn_events_memo() and not currently_events:
        db.set_warn_events_memo(False)

        text = """
AKTUALISIERUNG:
Der Deutsche Wetterdienst gibt f??r NRW zurzeit keine Warnungen der Kategorie 3 (rot) und 4 (violett) mehr aus -
also vor Unwetter oder extremem Unwetter. Damit besteht keine Warnpflicht mehr. Es kann allerdings nach wie vor
markante Wetterlagen geben - alle Informationen dazu auf einen Blick hier:

UWA-Karten: www.wdr.de/k/unwetterkarte
(Keine roten und violetten Unwettergebiete)

https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html
(Vgl. NRW auf Website des Deutschen Wetterdienstes)
""".strip()

        keywords = "Unwetter, UWA, Keine Warnpflicht"

        title_wina = "Amtliche Unwetterwarnung des DWD (UWA) - Warnpflicht aufgehoben"
        wina.upload_text(title_wina, text, keywords)

        title_slack = "Warnpflicht f??r NRW aufgehoben"
        slack.post_text(title_slack, text)

        print("No active events: warn_events_memo OFF")


@sched.scheduled_job("cron", hour=1)
def clean_old_events():
    cutoff = dt.datetime.now() - dt.timedelta(days=30)
    print("Deleting events from before", cutoff)
    print("Number of events currently in DB:", db.collection.count())

    res = db.collection.delete_many({"sent": {"$lt": cutoff}})
    print("Deleted", res.deleted_count, "events")

    print("Number of events left in DB:", db.collection.count())


@sched.scheduled_job("cron", hour=18)
def send_alive_message():
    alive_message = "Nicht senden - Statusmeldung: UWA aktiv.\n\nBitte beachten sie eventuell g??ltige Unwetterwarnungen."
    wina.upload_text(
        "Nicht senden - Statusmeldung: UWA aktiv",
        alive_message,
        "UWA-BUND, Statusmeldung",
    )
    slack.post_message(alive_message)


sched.start()

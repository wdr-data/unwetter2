#!/user/bin/env python3.6

import os
from datetime import datetime, timezone

import pytz
from feedgen.feed import FeedGenerator
from flask import Flask, Response, request, json, send_from_directory

from unwetter import db, generate, wina as wina_gen, sentry, config
from unwetter.generate import urls


sentry.init()
app = Flask(__name__, static_folder="website/build")


@app.route("/feed.rss")
def feed():
    fg = FeedGenerator()
    fg.id(urls.URL_BASE)
    fg.title("Unwetter-Bund")
    fg.link(
        href="https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html",
        rel="alternate",
    )
    fg.subtitle("Amtliche Unwetterwarnungen der Stufen 3 und 4")
    fg.link(href=f"{urls.URL_BASE}feed.rss", rel="self")
    fg.language("de")

    # Iterate over the most recent 5 events matching filter
    for event in db.load_published(limit=50):
        fe = fg.add_entry(order="append")
        fe.id(event["id"])
        fe.title(generate.title(event, variant="wina_headline"))
        fe.link(href=urls.wina(event))
        fe.published(event["sent"].replace(tzinfo=pytz.UTC))
        fe.description(generate.description(event).replace("\n", "<br>"))

    r = Response(fg.rss_str(pretty=True), mimetype="application/rss+xml")
    r.headers["Content-Type"] = "text/xml; charset=utf-8"
    return r


@app.route("/wina/<id>")
def wina(id):
    r = Response(wina_gen.from_id(id), mimetype="application/xml")
    r.headers["Content-Type"] = "text/xml; charset=iso-8859-1"

    return r


@app.route("/test")
def test():
    return "OK"


@app.route("/error")
def error():
    raise Exception("AHHHHHHHH")


@app.route("/api/v1/events/current", methods=["GET"])
def api_v1_current_events():
    at = request.args.get("at")

    if at:
        at = datetime.utcfromtimestamp(int(at))

    current_events = db.current_events(at=at, all_severities=True)
    filtered_events = []

    for event in current_events:
        if event["severity"] == "Minor":
            continue

        del event["_id"]
        del event["geometry"]
        for field in ("sent", "effective", "onset", "expires"):
            event[field] = event[field].replace(tzinfo=timezone.utc).timestamp()

        filtered_events.append(event)

    return json.dumps(sorted(filtered_events, key=config.severity_key, reverse=True))


# Serve React App
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

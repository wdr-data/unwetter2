import os

import sentry_sdk


def init():
    # TODO: Turn back on when we have a proper Sentry setup
    return

    sentry_sdk.init(
        os.environ.get("SENTRY_DSN"),
        release=os.environ.get("HEROKU_SLUG_COMMIT"),
    )

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag(
            "heroku-release",
            f"{os.environ.get('HEROKU_APP_NAME')}@{os.environ.get('HEROKU_RELEASE_VERSION')}",
        )

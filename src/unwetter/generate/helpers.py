#!/user/bin/env python3.9
import datetime as dt
from typing import List, Optional

import pytz


BERLIN = pytz.timezone("Europe/Berlin")
UTC = pytz.UTC


def local_now() -> dt.datetime:
    """Generate current datetime (Berlin time zone).

    Returns:
        dt.datetime: Current datetime.
    """
    return dt.datetime.now(tz=BERLIN)


def local_today() -> dt.date:
    """Generate current date (Berlin time zone).

    Returns:
        dt.date: Today's date.
    """
    return dt.datetime.now(BERLIN).date()


def local_yesterday() -> dt.date:
    """Generate yesterday's date (Berlin time zone).

    Returns:
        dt.date: Yesterday's date.
    """
    return local_today() - dt.timedelta(days=1)


def date_range(start: dt.date, end: dt.date) -> List[dt.date]:
    """Generate a list of dates within a range. Start and end are both
    inclusive.

    Args:
        start (dt.date): Start date for range.
        end (dt.date): End date for range.

    Returns:
        List[dt.date]: List of dates between start and end.
    """

    delta = (end - start).days
    return [start + dt.timedelta(days=delta_days) for delta_days in range(delta + 1)]


def to_timedelta(seconds: Optional[int]) -> Optional[dt.timedelta]:
    """Generate a timedelta from an int containing a number of seconds.

    Args:
        seconds (Optional[int]): Amount of seconds to convert to timedelta. Also
            accepts None as input.

    Returns:
        Optional[dt.timedelta]: timedelta - returns None if seconds are None.
    """
    if seconds is not None:
        return dt.timedelta(seconds=seconds)
    else:
        return None


def rreplace(s, old, new, occurrence=-1):
    """
    Replace old with new starting from end of the string
    :param s: The string to be transformed
    :param old: Search string
    :param new: Replacement string
    :param occurrence: Number of replacements to do
    :return:
    """
    li = s.rsplit(old, occurrence)
    return new.join(li)


def upper_first(s):
    if len(s) == 0:
        return s

    return s[0].upper() + s[1:]


def pad(text):
    return f"\n{text}\n"


def local_time(dt):
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(BERLIN)

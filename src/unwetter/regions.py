#!/user/bin/env python3.6

import yaml

from unwetter.data.districts import INVERSE_DISTRICTS


with open("config/regions.yml", "r") as fp:
    REGIONS = {
        key: value
        for key, value in yaml.safe_load(fp.read()).items()
        if value.get("districts")
    }

for name, region in REGIONS.items():
    region["name"] = name


def best_match(districts):
    """
    Takes a list of districts and finds the region(s) that contains them all and the coverage of
    those regions
    :param districts: List of district names
    :return: List of tuples of (region name, relevance)
    """

    if len(districts) == 0:
        return []

    return _best_match([district["warn_cell_id"] for district in districts])


def _cell_ids_for_region(region):
    return set(INVERSE_DISTRICTS[name] for name in region[1]["districts"])


def _best_match(district_ids):
    """
    Takes a list of district warn cell ids and finds the region(s) that contains
    them all and the coverage of those regions
    :param districts: List of district names
    :return: List of tuples of (region name, relevance)
    """

    district_ids_set = set(district_ids)

    def key_function(region):
        size = len(region[1]["districts"])
        not_covered = len(district_ids_set - _cell_ids_for_region(region))
        return not_covered, size

    match = sorted(REGIONS.items(), key=key_function)[0]
    match_cell_ids = _cell_ids_for_region(match)

    not_covered = len(district_ids_set - match_cell_ids)
    relevance = (len(district_ids) - not_covered) / len(match[1]["districts"])

    if not_covered == 0:
        return [(match[0], relevance)]
    elif not_covered == len(district_ids):
        print(f'Unknown districts "{[INVERSE_DISTRICTS[id] for id in district_ids]}"')
        return []
    else:
        return [(match[0], relevance)] + _best_match(district_ids_set - match_cell_ids)

#!/usr/bin/env python3
import csv
import json
import logging
import math
import os
import sys

import pygal

import scraping


logger = logging.getLogger(__name__)


def get_badge_data_and_writer(badge_id, filename):
    os.makedirs('data', exist_ok=True)

    try:
        f = open('data/' + filename + '.json', 'rt') 
    except IOError:
        f = None

    if f:
        with f:
            badge_data = scraping.BadgeData.from_json(json.load(f))
    else:
        badge_data = scraping.BadgeData(
            host='stackoverflow.com', badge_id=badge_id)

    print("Loaded {} {}s.".format(len(badge_data), filename))

    def write():
        with open('data/' + filename + '.json', 'wt') as f:
            json.dump(badge_data.to_json(), f)

    return badge_data, write


def main(*args):
    logging.basicConfig(level=logging.DEBUG)

    flags = set(args)

    so_sheriffs, write_sherrifs = get_badge_data_and_writer(
        badge_id=3109, filename='sherrif')
    so_constituents, write_constituents = get_badge_data_and_writer(
        badge_id=1974, filename='constituent')
    so_caucus, write_caucus = get_badge_data_and_writer(
        badge_id=1973, filename='caucus')

    so_sheriffs.update()
    write_sherrifs()

    so_constituents.update(stop_on_existing=bool(
        flags.intersection(['-x', '--stop-on-existing'])))
    write_constituents()

    so_caucus.update(stop_on_existing=bool(
        flags.intersection(['-x', '--stop-on-existing'])))
    write_caucus()

    constituents_by_reason = so_constituents.by_reason()
    caucus_by_reason = so_caucus.by_reason()

    assert len(constituents_by_reason) == len(caucus_by_reason)

    latest_constituents = constituents_by_reason[
        'for an <a href="/election/6">election</a>']

    first_vote_timestamp = latest_constituents[0].timestamp
    last_vote_timestamp = latest_constituents[0].timestamp

    hour_duration = 60 * 60
    votes_by_hour = [
        0 for _ in range(int(1 + math.floor(last_vote_timestamp - first_vote_timestamp)))]

    for badge in latest_constituents:
        i = int(math.floor((badge.timestamp - first_vote_timestamp) / hour_duration))
        votes_by_hour[i] += 1 

    chart = pygal.StackedLine()
    chart.add('votes by hour', votes_by_hour)
    chart.render_to_file('data/latest-election-cumulative.svg')
    print("wrote data/latest-election-cumulative.svg")

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

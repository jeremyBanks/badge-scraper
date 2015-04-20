#!/usr/bin/env python3
import csv
import lzma
import bz2
import gzip
import json
import logging
import math
import os
import sys

import pygal

import scraping


logger = logging.getLogger(__name__)


def get_badge_data_and_write_function(badge_id, filename):
    os.makedirs('data', exist_ok=True)

    logger.info("Loading {} badges...".format(filename))

    try:
        f = lzma.open('data/' + filename + '.json.xz', 'rt') 
    except FileNotFoundError:
        try:
            f = lzma.open('data/' + filename + '.json.lzma', 'rt') 
        except FileNotFoundError:
            try:
                f = bz2.open('data/' + filename + '.json.bz2', 'rt') 
            except FileNotFoundError:
                try:
                    f = gzip.open('data/' + filename + '.json.gz', 'rt') 
                except FileNotFoundError:
                    try:
                        f = open('data/' + filename + '.json', 'rt') 
                    except FileNotFoundError:
                        f = None

    if f:
        with f:
            badge_data = scraping.BadgeData.from_json(json.load(f))
    else:
        badge_data = scraping.BadgeData(
            host='stackoverflow.com', badge_id=badge_id)

    logger.info("...loaded {} {} badges.".format(len(badge_data), filename))

    def write():
        logger.info("Writing {} {} badges...".format(len(badge_data), filename))
        with lzma.open('data/' + filename + '.json.xz', 'wt') as f:
            json.dump(badge_data.to_json(), f)
        logger.info("...wrote {} {} badges.".format(len(badge_data), filename))

    return badge_data, write


def main(*args):
    logging.basicConfig(level=logging.DEBUG)

    flags = set(args)

    so_sheriffs, write_sherrifs = get_badge_data_and_write_function(
        badge_id=3109, filename='sherrif')
    so_constituents, write_constituents = get_badge_data_and_write_function(
        badge_id=1974, filename='constituent')
    so_caucus, write_caucus = get_badge_data_and_write_function(
        badge_id=1973, filename='caucus')

    so_sheriffs.update()
    write_sherrifs()

    so_constituents.update(stop_on_existing=bool(
        flags.intersection(['-x', '--stop-on-existing'])))

    so_caucus.update(stop_on_existing=bool(
        flags.intersection(['-x', '--stop-on-existing'])))

    constituents_by_reason = so_constituents.by_reason()
    caucus_by_reason = so_caucus.by_reason()

    assert len(constituents_by_reason) == len(caucus_by_reason)

    latest_constituents = constituents_by_reason[
        'for an <a href="/election/6">election</a>']
    latest_caucus = caucus_by_reason[
        'for an <a href="/election/6">election</a>']

    hour_duration = 60 * 60

    election_start_timestamp = min(
        badge.timestamp for badge in latest_constituents + latest_caucus)
    election_end_timestamp = max(
        badge.timestamp for badge in latest_constituents + latest_caucus)
    election_hours = int(
        1 + math.floor(election_end_timestamp - election_start_timestamp) /
        hour_duration)

    constituents_by_hour = [0 for _ in range(election_hours)]

    for badge in latest_constituents:
        constituents_by_hour[int(math.floor(badge.timestamp /  hour_duration))] += 1

    caucus_by_hour = [0 for _ in range(election_hours)]

    for badge in latest_caucus:
        caucus_by_hour[int(math.floor(badge.timestamp /  hour_duration))] += 1

    chart = pygal.Line(
        title="Latest Election Activity by Hour",
        y_title="Users",
        x_title="Hour",
        interpolate='cubic')
    chart.add('constituents', constituent_by_hour)
    chart.add('caucus', caucus_by_hour)

    chart.render_to_file('data/latest-election.svg')
    logger.info("wrote data/latest-election.svg")
    
    write_constituents()
    write_caucus()

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

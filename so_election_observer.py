#!/usr/bin/env python3
import csv
import json
import logging
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

    def write():
        with open('data/' + filename + '.json', 'wt') as f:
            json.dump(badge_data.to_json(), f, indent=2)

    return badge_data, write


def main(*args):
    logging.basicConfig(level=logging.DEBUG)

    logger.warn("This data seems very questionable.")

    flags = set(args)

    so_sheriffs, write_sherrifs = get_badge_data_and_writer(
        badge_id=3109, filename='sherrif')
    so_constituents, write_constituents = get_badge_data_and_writer(
        badge_id=1974, filename='constituents')
    so_caucus, write_caucus = get_badge_data_and_writer(
        badge_id=1974, filename='caucus')

    so_sheriffs.update()
    write_sherrifs()

    so_constituents.update(stop_on_existing=bool(
        flags.intersection(['-x', '--stop-on-existing'])))
    write_constituents()

    so_caucus.update(stop_on_existing=bool(
        flags.intersection(['-x', '--stop-on-existing'])))
    write_caucus()

    noise_limit = 128

    print("Stack Overfow's Sheriffs ==", list(so_sheriffs))
    print()
    
    constituents_by_election = so_constituents.grouped_by_timestamp(
        drop_groups_of_fewer_than=noise_limit)
    caucus_by_election = so_caucus.grouped_by_timestamp(
        drop_groups_of_fewer_than=noise_limit)

    assert len(constituents_by_election) == len(caucus_by_election)

    print("Info by election:")
    for n, (did, could) in enumerate(
            zip(constituents_by_election, caucus_by_election),
            start=2):
        print(
            "  {:2d}: {:7d} ({:4.1f}%) constituents out of {:8d} caucus"
            .format(
                n, len(did), 100 * (len(did) / len(could)), len(could)))
    print("Total:", len(so_constituents))
    print()

    latest_election_constituents = constituents_by_election[-1]
    latest_election_caucus = caucus_by_election[-1]

    voting_start_timestamp = latest_election_caucus[0].timestamp

    print("Saving latest-election-cumulative.csv")
    with open('data/latest-election-cumulative.csv', 'wt') as f:
        writer = csv.writer(f)
        writer.writerow(('time offset', 'cumulative votes'))

        for vote_count, badge in enumerate(latest_election_constituents, start=1):
            vote_offset = badge.timestamp - voting_start_timestamp
            writer.writerow((vote_offset, vote_count))

    print("Saving latest-election-cumulative-caucus.csv")
    with open('data/latest-election-cumulative-cacus.csv', 'wt') as f:
        writer = csv.writer(f)
        writer.writerow(('time offset', 'cumulative caucused'))

        for caucus_count, badge in enumerate(latest_election_caucus, start=1):
            caucus_offset = badge.timestamp - voting_start_timestamp
            writer.writerow((caucus_offset, caucus_count))

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

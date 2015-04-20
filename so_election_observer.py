#!/usr/bin/env python3
import csv
import logging
import sys

import scraping


logger = logging.getLogger(__name__)


def main(*args):
    logging.basicConfig(level=logging.DEBUG)

    logger.warn("This data seems very questionable.")
    
    flags = set(args)

    so_sheriffs = scraping.BadgeData(
        host='stackoverflow.com', badge_id=3109, filename='sheriffs.csv')
    so_constituents = scraping.BadgeData(
        host='stackoverflow.com', badge_id=1974, filename='constituents.csv')
    so_caucus = scraping.BadgeData(
        host='stackoverflow.com', badge_id=1973, filename='caucus.csv')

    noise_limit = 128

    for badge_data in [so_constituents , so_caucus]:
        badge_data.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))

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
    with open('latest-election-cumulative.csv', 'wt') as f:
        writer = csv.writer(f)
        writer.writerow(('time offset', 'cumulative votes'))

        for vote_count, badge in enumerate(latest_election_constituents, start=1):
            vote_offset = badge.timestamp - voting_start_timestamp
            writer.writerow((vote_offset, vote_count))

    print("Saving latest-election-cumulative-caucus.csv")
    with open('latest-election-cumulative-cacus.csv', 'wt') as f:
        writer = csv.writer(f)
        writer.writerow(('time offset', 'cumulative caucused'))

        for caucus_count, badge in enumerate(latest_election_caucus, start=1):
            caucus_offset = badge.timestamp - voting_start_timestamp
            writer.writerow((caucus_offset, caucus_count))

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

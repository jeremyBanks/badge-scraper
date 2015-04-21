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
import time

import pygal

import scraping


logger = logging.getLogger(__name__)


class ElectionData(object):
    def __init__(self, constituent_badges, caucus_badges):
        reason_html = constituent_badges[0].reason_html

        for badge in constituent_badges:
            assert reason_html == badge.reason_html

        for badge in caucus_badges:
            assert reason_html == badge.reason_html

        self.id = int(
            reason_html
            .partition('/election/')[2]
            .partition('"')[0])
        self.constituent_badges = constituent_badges
        self.caucus_badges = caucus_badges

        self.start_timestamp = self.caucus_badges[0].timestamp
        self.election_timestamp = self.constituent_badges[0].timestamp

        # We can't just look at the data, because there are some
        # badges awarded later than makes sense. Hope this doesn't
        # change.
        self.end_timestamp = self.start_timestamp + 15 * 24 * 60 * 60

        self._prepare_data()

    def _prepare_data(self):
        logger.info(
            "Generating graphs for election {}.".format(self.id))

        self.hour_duration = 60 * 60
        self.election_hours = int(
            1 + math.floor(self.end_timestamp - self.start_timestamp) /
            self.hour_duration)

        self.constituents_by_hour = [0 for _ in range(self.election_hours)]
        self.first_constituent_index = len(self.constituents_by_hour)
        for badge in self.constituent_badges:
            index = int(math.floor(
                (badge.timestamp - self.start_timestamp) /
                self.hour_duration))
            if index < self.first_constituent_index:
                self.first_constituent_index = index
            try:
                self.constituents_by_hour[index] += 1
            except IndexError:
                logger.debug("ignoring weird {!r}".format(badge))

        self.caucus_by_hour = [0 for _ in range(self.election_hours)]
        for badge in self.caucus_badges:
            try:
                self.caucus_by_hour[
                    int(math.floor(
                        (badge.timestamp - self.start_timestamp) /
                        self.hour_duration))] += 1
            except IndexError:
                logger.debug("ignoring weird {!r}".format(badge))

    def hello_graphs(self):
        filename = 'images/election-{}-both-per-hour.svg'.format(self.id)
        logger.info("Generating {}.".format(filename))

        chart = pygal.Line(
            title="Election {} Participation Per Hour".format(self.id),
            y_title="Users",
            show_dots=False,
            width=1024,
            height=768,
            range=(0, 1000),
            value_formatter=lambda n: str(int(n)),
            legend_at_bottom=True)

        chart.add('constituents', self.constituents_by_hour)
        chart.add('caucus', self.caucus_by_hour)

        chart.render_to_file(filename)
        logger.info("Wrote {}.".format(filename))


        filename = 'images/election-{}-constituents-per-hour.svg'.format(self.id)
        logger.info("Generating {}.".format(filename))
        chart = pygal.Line(
            title="Election {} Constituents Per Hour".format(self.id),
            y_title="Users",
            show_dots=False,
            width=1024,
            height=768,
            range=(0, 1000),
            value_formatter=lambda n: str(int(n)),
            legend_at_bottom=True)

        chart.add(
            'constituents', self.constituents_by_hour[
                self.first_constituent_index:])

        chart.render_to_file(filename)
        logger.info("Wrote {}.".format(filename))

        filename = 'images/election-{}-both-cumulative.svg'.format(self.id)
        logger.info("Generating {}.".format(filename))

        chart = pygal.Line(
            title="Election {} Participation".format(self.id),
            y_title="Users",
            show_dots=False,
            width=1024,
            height=768,
            value_formatter=lambda n: str(int(n)),
            legend_at_bottom=True)

        chart.add('constituents', list(sums(self.constituents_by_hour)))
        chart.add('caucus', list(sums(self.caucus_by_hour)))

        chart.render_to_file(filename)
        logger.info("Wrote {}.".format(filename))


def main(*args):
    flags = set(args)
    assert not flags - {
        '-n', '--no-update', '-e', '--forever', '-m', '--no-write' }

    os.makedirs('data', exist_ok=True)
    os.makedirs('images', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='\n'
               '    ' + '_' * 76 + '\n'
               '    | %(asctime)23s %(pathname)44s:%(lineno)-4s \n'
               '____| %(levelname)-10s           %(name)51s \n'
               '\n'
               '%(message)s')

    so_sheriffs, write_sherrifs = get_badge_data_and_write_function(
        badge_id=3109, filename='sherrif')
    so_constituents, write_constituents = get_badge_data_and_write_function(
        badge_id=1974, filename='constituent')
    so_caucus, write_caucus = get_badge_data_and_write_function(
        badge_id=1973, filename='caucus')

    while True:
        if not flags.intersection(['-n', '--no-update']):
            so_sheriffs.update()
            if not flags.intersection(['-m', '--no-write']):
                write_sherrifs()

            so_constituents.update()
            so_caucus.update()

        logger.info("Grouping constituents by election.")
        constituents_by_reason = so_constituents.by_reason()
        
        logger.info("Grouping caucuses by election.")
        caucus_by_reason = so_caucus.by_reason()

        elections = {}

        for reason in constituents_by_reason:
            election = ElectionData(
                constituent_badges=constituents_by_reason[reason],
                caucus_badges=caucus_by_reason[reason])
            assert elections.get(election.id) is None
            elections[election.id] = election

            election.hello_graphs()

        filename = 'images/election-5-6-both-cumulative.svg'
        logger.info("Generating {}.".format(filename))

        chart = pygal.Line(
            title="Election 5 and 6 Participation",
            y_title="Users",
            show_dots=False,
            width=1024,
            height=768,
            value_formatter=lambda n: str(int(n)),
            legend_at_bottom=True)

        chart.add(
            '5 constituents', list(sums(elections[5].constituents_by_hour)))
        chart.add(
            '5 caucus', list(sums(elections[5].caucus_by_hour)))

        chart.add(
            '6 constituents', list(sums(elections[6].constituents_by_hour)))
        chart.add(
            '6 caucus', list(sums(elections[6].caucus_by_hour)))

        chart.render_to_file(filename)
        logger.info("Wrote {}.".format(filename))

        if not flags.intersection(['-n', '--no-update', '-m', '--no-write']):
            write_constituents()
            write_caucus()

        if not flags.intersection(['-e', '--forever']):
            break

        logger.info("Sleeping for a while")
        time.sleep(60 * 5)


def sums(xs):
    n = 0
    for x in xs:
        n += x
        yield n


def get_badge_data_and_write_function(badge_id, filename, require_file=False):
    logger.info("Loading {} badges...".format(filename))

    try:
        f = lzma.open('data/' + filename + '.json.xz', 'rt') 
    except FileNotFoundError:
        try:
            f = open('data/' + filename + '.json', 'rt') 
        except FileNotFoundError:
            if not require_file:
                f = None
            else:
                raise

    if f:
        with f:
            badge_data = scraping.BadgeData.from_json(json.load(f))
    else:
        badge_data = scraping.BadgeData(
            host='stackoverflow.com', badge_id=badge_id)

    logger.info("...{} {} badges loaded.".format(len(badge_data), filename))

    def write():
        logger.info("Writing {} {} badges...".format(len(badge_data), filename))
        with lzma.open('data/' + filename + '.json.xz', 'wt') as f:
            json.dump(badge_data.to_json(), f)
        logger.info("...wrote {} {} badges.".format(len(badge_data), filename))

    return badge_data, write


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

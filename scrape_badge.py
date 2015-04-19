#!/usr/bin/env python3
import collections.abc
import csv
import itertools
import logging
import sys
import time

import requests


class BadgeData(object):
    """Scrapes and persists a record of all instances of a particular
    badge that have been awarded on a Stack Exchange site.
    """

    FIELD_NAMES = 'user_id', 'utc_time'
    REQUEST_INTERVAL_SECONDS = 2.0
    logger = logging.getLogger(__name__).getChild('BadgeData')

    def __init__(self, host, badge_id, filename):
        self.host = host
        self.badge_id = badge_id
        self.filename = filename

        self.instances = set()
        self.load()

    def load(self):
        """Loads any existing data from the associated CSV file."""
        try:
            f = open(self.filename, 'rt+', newline='')
        except IOError as ex:
            f = None

        if f is not None:
            with f:
                reader = csv.reader(f)
                try:
                    header_row = tuple(next(reader))
                except StopIteration:
                    self.logger.warn(
                        "Existing badge data file exists but is empty. "
                        "Adding header row.")
                    f.seek(0)
                    writer = csv.writer(f)
                    writer.writerow(self.FIELD_NAMES)

                    return

                if header_row != self.FIELD_NAMES:
                    raise ValueError(
                        "Expected field names {!r}, found {!r}.".format(
                            self.FIELD_NAMES, header_row))

                for row in reader:
                    user_id, utc_time = row
                    self.instances.add(Badge(
                        badge_id=self.badge_id,
                        user_id=int(user_id),
                        utc_time=utc_time))

            self.logger.info(
                "Read %s instances from badge data file.", len(self.instances))
        else:
            self.logger.info(
                "There is no existing badge data file. "
                "Creating one with header.")

            with open(self.filename, 'wt') as f:
                writer = csv.writer(f)
                writer.writerow(self.FIELD_NAMES)


    def update(self):
        """Scrape the site, saving all new badge instances to the data file."""

        try:
            f = open(self.filename, 'at', newline='')
            new_file = False
        except IOError as ex:
            f = open(self.filename, 'wt', newline='')
            new_file = True

        with f:
            writer = csv.writer(f)

            if new_file:
                writer.writerow(self.FIELD_NAMES)

            for badge in self._scrape_all_badges():
                if badge not in self.instances:
                    writer.writerow((badge.user_id, badge.utc_time))
                    self.instances.add(badge)
                    self.logger.info("Scraped badge: %r.", badge)
                else:
                    self.logger.warn("Scraped already-known badge %r.", badge)

            self.logger.info("Reached end of badge list. Update complete.")

    def _scrape_all_badges(self):
        """Yields instances of all badges on the site, scraping them
        one page at a time.
        """

        for page_number in itertools.count(1):
            time.sleep(self.REQUEST_INTERVAL_SECONDS)
            url = 'http://{}/help/badges/{}?page={}'.format(
                self.host, self.badge_id, page_number)

            html = requests.get(url).text

            # HACK(TO͇̹̺ͅƝ̴ȳ̳ TH̘Ë͖́̉ ͠P̯͍̭O̚​N̐Y̡)

            page_count = int(html
                .rpartition('<span class="page-numbers">')[2]
                .partition('<')[0])

            if page_number > page_count:
                logger.info("Reached end of list; page does not exist.")
                break

            without_leading_crap = html.partition(
                '<div class="single-badge-table')[2]
            also_without_trailing_crap = without_leading_crap.partition(
                '<div class="pager')[0]
            row_pieces = also_without_trailing_crap.split(
                '<div class="single-badge-row-reason')[1:]

            for row_piece in row_pieces:
                user_id = int((row_piece
                    .partition('<a href="/users/')[2]
                    .partition('/')[0]))
                utc_time = (row_piece
                    .partition('Awarded <span title="')[2]
                    .partition('"')[0])

                yield Badge(
                    badge_id=self.badge_id, user_id=user_id, utc_time=utc_time)

            self.logger.debug("Scraped page %s/%s.", page_number, page_count)

class Badge(collections.abc.Hashable):
    """An awarded instance of a particular badge."""

    def __init__(self, badge_id, user_id, utc_time):
        self.badge_id = badge_id
        self.user_id = user_id
        self.utc_time = utc_time

    def __eq__(self, other):
        return (self.badge_id == other.badge_id and
                self.user_id == other.user_id and
                self.utc_time == other.utc_time)

    def __hash__(self):
        return hash((self.badge_id, self.user_id, self.utc_time))

    def __repr__(self):
        return ('{0.__class__.__name__}(badge_id={0.badge_id!r}, '
                'user_id={0.user_id!r}, utc_time={0.utc_time!r}'
                .format(self))


def main():
    logging.basicConfig(level=logging.DEBUG)
    so_constituents = BadgeData(
        host='stackoverflow.com', badge_id=1974, filename='constituents.csv')
    so_constituents.update()


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

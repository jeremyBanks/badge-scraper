#!/usr/bin/env python3
import calendar
import collections.abc
import datetime
import itertools
import logging
import time

import requests


logger = logging.getLogger(__name__)


def timestamp_from_iso1608(s):
    """Returns the unix timestamp for a Stack Exchange ISO 1608 date/time."""
    return calendar.timegm(
        datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%SZ').timetuple())


class BadgeData(collections.abc.Iterable):
    """Scrapes and persists a record of all instances of a particular
    badge that have been awarded on a Stack Exchange site.

    Iteration over BadgeData yields all instances in chronological order.
    """

    FIELD_NAMES = 'user_id', 'utc_time'
    REQUEST_INTERVAL_SECONDS = .5
    logger = logging.getLogger(__name__).getChild('BadgeData')

    def __init__(self, host, badge_id, filename):
        self.host = host
        self.badge_id = badge_id
        self.filename = filename

        self._instances = set()
        self.load()

    def __repr__(self):
        return (
            '<{0.__class__.__name__} for {0.host}/badges/{0.badge_id} with {1} '
            'instances>'.format(self, len(self._instances)))

    def __iter__(self):
        return iter(sorted(self._instances, key=lambda badge: badge.timestamp))

    def __len__(self):
        return len(self._instances)

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
                    user_id, timestamp_raw = row

                    try:
                        timestamp = int(timestamp_raw)
                    except ValueError:
                        timestamp = timestamp_from_iso1608(timestamp_raw)

                    self._instances.add(Badge(
                        badge_id=self.badge_id,
                        user_id=int(user_id),
                        timestamp=timestamp))

            self.logger.info(
                "Read %s instances from data file for %s.",
                len(self._instances), self)
        else:
            self.logger.info(
                "There is no existing badge data file. "
                "Creating one with header.")

            with open(self.filename, 'wt') as f:
                writer = csv.writer(f)
                writer.writerow(self.FIELD_NAMES)

    def update(self, stop_on_existing=False):
        """Scrape the site, saving all new badge instances to the data file.

        If stop_on_existing is True, this will stop scraping once it sees see a
        badge that has already been recorded. Otherwise, it will continue.

        stop_on_existing should be specified if you know that self._instances
        contains *all* instances up to any specific point in time.
        PLEASE NOTE that BadgeData's implementation does not guarauntee this
        if an update() has been interrupted.
        """

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
                if badge not in self._instances:
                    writer.writerow((badge.user_id, badge.timestamp))
                    self._instances.add(badge)
                    self.logger.info("Scraped badge: %r.", badge)
                else:
                    self.logger.info("Scraped already-known badge %r.", badge)

                    if stop_on_existing:
                        return

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
                self.logger.info("Reached end of list; page does not exist.")
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
                timestamp_raw = (row_piece
                    .partition('Awarded <span title="')[2]
                    .partition('"')[0])
                timestamp = timestamp_from_iso1608(timestamp_raw)

                yield Badge(
                    badge_id=self.badge_id, user_id=user_id, timestamp=timestamp)

            self.logger.debug("Scraped page %s/%s.", page_number, page_count)

    def grouped_by_timestamp(self, group_duration=7 * 24 * 60 * 60):
        groups = []
        latest_timestamp = -1

        for badge in self:
            if badge.timestamp < latest_timestamp + group_duration:
                groups[-1].append(badge)
            else:
                groups.append([badge])

            latest_timestamp = badge.timestamp

        return groups


class Badge(collections.abc.Hashable):
    """An awarded instance of a particular badge."""

    def __init__(self, badge_id, user_id, timestamp):
        self.badge_id = badge_id
        self.user_id = user_id
        self.timestamp = timestamp

    def __eq__(self, other):
        return (self.badge_id == other.badge_id and
                self.user_id == other.user_id and
                self.timestamp == other.timestamp)

    def __hash__(self):
        return hash((self.badge_id, self.user_id, self.timestamp))

    def __repr__(self):
        return ('{0.__class__.__name__}(badge_id={0.badge_id!r}, '
                'user_id={0.user_id!r}, timestamp={0.timestamp!r})'
                .format(self))


def main(*args):
    logger.warn("This data seems very questionable.")

    flags = set(args)
    logging.basicConfig(level=logging.DEBUG)

    so_sheriffs = BadgeData(
        host='stackoverflow.com', badge_id=3109, filename='sheriffs.csv')
    so_constituents = BadgeData(
        host='stackoverflow.com', badge_id=1974, filename='constituents.csv')
    so_caucus = BadgeData(
        host='stackoverflow.com', badge_id=1973, filename='caucus.csv')

    for badge_data in [so_sheriffs, so_constituents , so_caucus]:
        badge_data.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))

    print("Stack Overfow's Sheriffs ==", list(so_sheriffs))
    print()
    
    constituents_by_election = so_constituents.grouped_by_timestamp()
    caucus_by_election = so_caucus.grouped_by_timestamp()

    print("Voters by election:")
    for n, badges in enumerate(constituents_by_election, start=1):
        print("  {}: {}".format(n, len(badges)))
    print("Total:", len(so_constituents))
    print()
    print("Visited caucus by election:")
    for n, badges in enumerate(caucus_by_election, start=1):
        print("  {}: {}".format(n, len(badges)))
    print("Total:", len(so_caucus))
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

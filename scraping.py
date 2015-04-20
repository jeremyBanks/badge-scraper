#!/usr/bin/env python3
import calendar
import collections.abc
import csv
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

    def __init__(self, host, badge_id, instances=()):
        self.host = host
        self.badge_id = badge_id
        self._instances = set(instances)

    def to_json(self):
        return {
            'host': self.host,
            'badge_id': self.badge_id,
            'instances': [ instance.to_json() for instance in self ]
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            host=data['host'],
            badge_id=data['badge_id'],
            instances=[
                Badge.from_json(instance_data, badge_id=data['badge_id'])
                for instance_data in data['instances']])

    def __repr__(self):
        return (
            '<{0.__class__.__name__} for {0.host}/badges/{0.badge_id} with {1} '
            'instances>'.format(self, len(self._instances)))

    def __iter__(self):
        return iter(sorted(self._instances, key=lambda badge: badge.timestamp))

    def __len__(self):
        return len(self._instances)

    def update(self, stop_on_existing=False):
        """Scrape the site, saving all new badge instances to the data file.

        If stop_on_existing is True, this will stop scraping once it sees see a
        badge that has already been recorded. Otherwise, it will continue.

        stop_on_existing should be specified if you know that self._instances
        contains *all* instances up to any specific point in time.
        PLEASE NOTE that BadgeData's implementation does not guarauntee this
        if an update() has been interrupted.
        """

        previously_existing = set(self._instances)

        for badge in self._scrape_all_badges():
            if badge not in self._instances:
                self._instances.add(badge)
                self.logger.info("Scraped badge: %r.", badge)
            elif badge in previously_existing:
                self.logger.info("Scraped already-known badge %r.", badge)
                return
            # else it's probably slight page overlap from data changing

        self.logger.info("Reached end of badge list. Update complete.")

    def _scrape_all_badges(self):
        """Yields instances of all badges on the site, scraping them
        one page at a time. May return duplicates.
        """

        page_count_values = []

        for page_number in itertools.count(1):
            # FIXME
            time.sleep(self.REQUEST_INTERVAL_SECONDS)

            url = 'http://{}/help/badges/{}?page={}'.format(
                self.host, self.badge_id, page_number)

            response = requests.get(url)
            yield from self._scrape_response(response, page_count_values)

            if page_number > page_count_values[-1]:
                self.logger.info("Reached end of list.")
                return

            self.logger.debug(
                "Scraped page %s/%s", page_number, page_count_values[-1])

    def _scrape_response(self, response, page_count_values=None):
        page_count_raw = (response.text
            .rpartition('<span class="page-numbers">')[2]
            .partition('<')[0])
        page_count = int(page_count_raw) if page_count_raw else 1
        if page_count_values is not None:
            page_count_values.append(page_count)

        without_leading_crap = response.text.partition(
            '<div class="single-badge-table')[2]
        also_without_trailing_crap = without_leading_crap.partition(
            '<div class="pager')[0]
        row_pieces = also_without_trailing_crap.split(
            '<div class="single-badge-row-')[1:]

        for row_piece in row_pieces:
            yield Badge(badge_id=self.badge_id, html=row_piece)

    def by_reason(self):
        by_reason = {}

        for badge in self:
            by_reason.setdefault(badge.for_what, []).append(badge)

        return by_reason


class Badge(collections.abc.Hashable):
    """An awarded instance of a particular badge."""

    def __init__(self, badge_id, html):
        self.badge_id = badge_id
        self.html = html

    @property
    def user_id(self):
        return int((self.html
            .partition('<a href="/users/')[2]
            .partition('/')[0]))

    @property
    def stack_time(self):
        return (self.html
            .partition('Awarded <span title="')[2]
            .partition('"')[0])

    @property
    def timestamp(self):
        return timestamp_from_iso1608(self.stack_time)

    @property
    def for_what(self):
        reason_part = (self.html
            .partition('<div class="single-badge-reason">')[2]
            .partition('</div>')[0])

        return reason_part.strip() or None

    @classmethod
    def from_json(cls, data, badge_id):
        self = Badge(
            badge_id=badge_id,
            html=data['html'])

        assert self.for_what == data['for_what']
        assert self.timestamp == data['timestamp']
        assert self.stack_time == data['stack_time']

        return self

    def to_json(self):
        return {
            'user_id': self.user_id,
            'html': self.html,
            'for_what': self.for_what,
            'stack_time': self.stack_time,
            'timestamp': self.timestamp
        } 

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


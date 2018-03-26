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
    REQUEST_INTERVAL_SECONDS = 0.5
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
                self.logger.debug("Scraped badge: %r.", badge)
            elif badge in previously_existing:
                self.logger.debug("Scraped already-known badge %r.", badge)
                return
            # else it's probably slight page overlap from data changing

        self.logger.info("Reached end of badge list. Update complete.")

    def _scrape_all_badges(self):
        """Yields instances of all badges on the site, scraping them
        one page at a time. May return duplicates.
        """

        page_count_values = []
        start_time = time.time()

        for page_number in itertools.count(1):
            # FIXME
            time.sleep(self.REQUEST_INTERVAL_SECONDS)

            url = 'https://{}/help/badges/{}?page={}'.format(
                self.host, self.badge_id, page_number)

            response = requests.get(url)
            yield from self._scrape_response(response, page_count_values)

            if page_number > page_count_values[-1]:
                self.logger.info("Now past last page.")
                return

            eta = (
                (page_count_values[-1] - page_number) *
                ((time.time() - start_time) / page_number)) / 60

            self.logger.info(
                "Scraped page %s/%s (~%.1fm remaining)",
                page_number, page_count_values[-1], eta)

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
            by_reason.setdefault(badge.reason_html, []).append(badge)
        return by_reason

class Badge(collections.abc.Hashable):
    """An awarded instance of a particular badge."""

    def __init__(self, badge_id, html=None):
        self.badge_id = badge_id

        if html is not None:
            self.reason_html = (
                html
                .partition('<div class="single-badge-reason">')[2]
                .partition('</div>')[0]).strip() or None
            self.user_id = int(
                html
                .partition('<a href="/users/')[2]
                .partition('/')[0])
            self.stack_time = (
                html
                .partition('Awarded <span title="')[2]
                .partition('"')[0]) or None
            self.timestamp = timestamp_from_iso1608(self.stack_time)
            self.username_html = (
                html
                .partition('<a href="/users/')[2]
                .partition('>')[2]
                .partition('<')[0]) or None
            rep_piece = (
                html
                .partition('<span class="reputation-score"')[2]
                .partition('<')[0])
            rep_text = rep_piece.partition('>')[2]
            if 'k' not in rep_text:
                self.rep = int(rep_text.replace(',', ''))
            else:
                self.rep = int(
                    rep_piece
                    .partition('reputation score ')[2]
                    .partition('"')[0]
                    .replace(',', ''))
            self.gold = int(
                ' gold badge' in html and
                html
                .rpartition(' gold badge')[0]
                .rpartition('<span title="')[2]
                .replace(',', '')
                or 0)
            self.silver = int(
                ' silver badge' in html and
                html
                .rpartition(' silver badge')[0]
                .rpartition('<span title="')[2]
                .replace(',', '')
                or 0)
            self.bronze = int(
                ' bronze badge' in html and
                html
                .rpartition(' bronze badge')[0]
                .rpartition('<span title="')[2]
                .replace(',', '')
                or 0)

    @classmethod
    def from_json(cls, data, badge_id):
        self = Badge(badge_id=badge_id, html=data.get('html'))
        if 'html' not in data:
            self.reason_html = data['reason_html']
            self.user_id = data['user_id']
            self.username_html = data['username_html']
            self.stack_time = data['stack_time']
            self.timestamp = data['timestamp']
            self.rep = data['rep']
            self.gold = data['gold']
            self.silver = data['silver']
            self.bronze = data['bronze']

        return self

    def to_json(self, html=True):
        if hasattr(self, 'html') and self.html is not None:
            return {
                'html': self.html
            }
        else:
            return {
                'reason_html': self.reason_html,
                'user_id': self.user_id,
                'stack_time': self.stack_time,
                'timestamp': self.timestamp,
                'username_html': self.username_html,
                'rep': self.rep,
                'gold': self.gold,
                'silver': self.silver,
                'bronze': self.bronze,
            }

    def __eq__(self, other):
        return (self.badge_id == other.badge_id and
                self.user_id == other.user_id and
                self.timestamp == other.timestamp and
                self.reason_html == other.reason_html)

    def __hash__(self):
        return hash((
            self.badge_id, self.user_id, self.timestamp, self.reason_html))

    def __repr__(self):
        return ('{0.__class__.__name__}(badge_id={0.badge_id!r}, '
                'user_id={0.user_id!r}, timestamp={0.timestamp!r})'
                .format(self))


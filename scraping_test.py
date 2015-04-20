#!/usr/bin/env python3
import logging

import pytest

import scraping


logger = logging.getLogger(__name__)


def test_timestamp_from_iso1608():
    f = scraping.timestamp_from_iso1608

    assert f('2015-04-20 01:00:15Z') == 1429491615

    assert f('1970-01-01 00:00:00Z') == 0

    with pytest.raises(Exception):
        f('hello world')


def test_can_scrape_caucus():
    import test_pages.so_help_badges_1973_caucus_x6dee

    host = 'stackoverflow.com'
    fake_badge = scraping.BadgeData(
        badge_id=1973, host=None, filename='/dev/null')

    page_count_values = []
    badges = list(fake_badge._scrape_response(
        response=test_pages.so_help_badges_1973_caucus_x6dee,
        page_count_values=page_count_values))

    assert page_count_values == [3710]
    assert len(badges) == 60


def test_can_scrape_constituent():
    import test_pages.so_help_badges_1974_constituent_x32ec

    host = 'stackoverflow.com'
    fake_badge = scraping.BadgeData(
        badge_id=1973, host=None, filename='/dev/null')

    page_count_values = []
    badges = list(fake_badge._scrape_response(
        response=test_pages.so_help_badges_1974_constituent_x32ec,
        page_count_values=page_count_values))

    assert page_count_values == [989]
    assert len(badges) == 60


def test_can_scrape_sheriff():
    import test_pages.so_help_badges_3109_sheriff_x58e7

    host = 'stackoverflow.com'
    fake_badge = scraping.BadgeData(
        badge_id=3109, host=None, filename='/dev/null')

    page_count_values = []
    badges = list(fake_badge._scrape_response(
        response=test_pages.so_help_badges_3109_sheriff_x58e7,
        page_count_values=page_count_values))

    assert page_count_values == [1]
    assert len(badges) == 60



def test_can_scrape_steward():
    import test_pages.so_help_badges_2279_steward_x0dca

    host = 'stackoverflow.com'
    fake_badge = scraping.BadgeData(
        badge_id=2279, host=None, filename='/dev/null')

    page_count_values = []
    badges = list(fake_badge._scrape_response(
        response=test_pages.so_help_badges_2279_steward_x0dca,
        page_count_values=page_count_values))

    assert page_count_values == [79]
    assert len(badges) == 60

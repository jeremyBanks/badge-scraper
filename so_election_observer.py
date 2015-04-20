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


LATEST_ELECTION_REASON = 'for an <a href="/election/6">election</a>'


def sums(xs):
    n = 0
    for x in xs:
        n += x
        yield n


def get_badge_data_and_write_function(badge_id, filename, require_file=False):
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
                        if not require_file or True:
                            f = None
                        else:
                            raise

    if f:
        with f:
            badge_data = scraping.BadgeData.from_json(json.load(f))
    else:
        badge_data = scraping.BadgeData(
            host='stackoverflow.com', badge_id=badge_id)

    logger.info("...{} loaded.".format(len(badge_data), filename))

    def write():
        logger.info("Writing {} {} badges...".format(len(badge_data), filename))
        with lzma.open('data/' + filename + '.json.xz', 'wt') as f:
            json.dump(badge_data.to_json(), f)
        logger.info("...wrote {} {} badges.".format(len(badge_data), filename))

    return badge_data, write


def main(*args):
    so_publicist, write_publicist = get_badge_data_and_write_function(
        badge_id=262, filename='publicist')
    write_publicist()

    return

    logging.basicConfig(
        level=logging.INFO,
        format='\n'
               '    ' + '_' * 76 + '\n'
               '    | %(asctime)23s %(pathname)44s:%(lineno)-4s \n'
               '____| %(levelname)-10s           %(name)51s \n'
               '\n'
               '%(message)s')

    flags = set(args)

    so_sheriffs, write_sherrifs = get_badge_data_and_write_function(
        badge_id=3109, filename='sherrif')
    so_constituents, write_constituents = get_badge_data_and_write_function(
        badge_id=1974, filename='constituent')
    so_caucus, write_caucus = get_badge_data_and_write_function(
        badge_id=1973, filename='caucus')
    so_steward, write_steward = get_badge_data_and_write_function(
        badge_id=2279, filename='steward')
    so_copy_editor, write_copy_editor = get_badge_data_and_write_function(
        badge_id=223, filename='copy_editor')
    so_publicist, write_publicist = get_badge_data_and_write_function(
        badge_id=262, filename='publicist')

    if not flags.intersection(['-n', '--no-update']):
        so_sheriffs.update()
        write_sherrifs()

        so_constituents.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))
        so_caucus.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))
        so_steward.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))
        so_copy_editor.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))
        so_publicist.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))

    logger.info("Grouping constituents by election.")
    constituents_by_reason = so_constituents.by_reason()
    
    logger.info("Grouping caucuses by election.")
    caucus_by_reason = so_caucus.by_reason()
    
    assert len(constituents_by_reason) == len(caucus_by_reason)

    latest_constituents = constituents_by_reason[LATEST_ELECTION_REASON]
    latest_caucus = caucus_by_reason[LATEST_ELECTION_REASON]

    chunk_duration = 60 * 60

    election_start_timestamp = min([
        latest_constituents[0].timestamp, latest_caucus[0].timestamp])
    election_end_timestamp = max([
        latest_constituents[-1].timestamp, latest_caucus[-1].timestamp])
    election_chunks = int(
        1 + math.floor(election_end_timestamp - election_start_timestamp) /
        chunk_duration)

    logger.info("Grouping constituent badges into chunks.")

    constituents_by_chunk = [0 for _ in range(election_chunks)]

    first_constituent_index = len(election_chunks)
    for badge in latest_constituents:
        index = int(math.floor(
            (badge.timestamp - election_start_timestamp) /
            chunk_duration))
        if index < first_constituent_index:
            first_constituent_index = index
        constituents_by_chunk[index] += 1

    logger.info("Grouping caucus badges into chunks.")

    caucus_by_chunk = [0 for _ in range(election_chunks)]

    for badge in latest_caucus:
        caucus_by_chunk[
            int(math.floor(
                (badge.timestamp - election_start_timestamp) /
                chunk_duration))] += 1

    logger.info("Generating data/latest-election.svg.")

    rate_chart = pygal.Line(
        title="Latest Election Participation Per Hour",
        y_title="Users",
        show_dots=False,
        range=(0, 512),
        width=1024,
        height=768,
        value_formatter=lambda n: str(int(n)),
        legend_at_bottom=True)

    rate_chart.add('constituents', constituents_by_chunk)
    rate_chart.add('caucus', caucus_by_chunk)

    rate_chart.render_to_file('data/latest-election.svg')
    logger.info("wrote data/latest-election.svg")

    logger.info("Generating data/latest-election-constituents.svg.")

    rate_chart = pygal.Line(
        title="Latest Election Constituents Per Hour",
        y_title="Users",
        show_dots=False,
        range=(0, 512),
        width=1024,
        height=768,
        value_formatter=lambda n: str(int(n)),
        legend_at_bottom=True)

    rate_chart.add(
        'constituents', constituents_by_chunk[first_constituent_index:])

    rate_chart.render_to_file('data/latest-election-constituents.svg')
    logger.info("wrote data/latest-election-constituents.svg")

    logger.info("Generating data/latest-election-sums.svg.")

    aggregate_chart = pygal.Line(
        title="Latest Election Participation",
        y_title="Users",
        show_dots=False,
        width=1024,
        height=768,
        value_formatter=lambda n: str(int(n)),
        legend_at_bottom=True)

    aggregate_chart.add('constituents', list(sums(constituents_by_chunk)))
    aggregate_chart.add('caucus', list(sums(caucus_by_chunk)))

    aggregate_chart.render_to_file('data/latest-election-sums.svg')
    logger.info("Wrote data/latest-election-sums.svg")

    if not flags.intersection(['-n', '--no-update']):
        write_constituents()
        write_caucus()
        write_steward()
        write_copy_editor()
        write_publicist()

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

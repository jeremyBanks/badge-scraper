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
    logging.basicConfig(
        level=logging.DEBUG,
        format='\n'
               '  ' + '_' * 76 + '  \n'
               '  | %(asctime)23s %(pathname)44s:%(lineno)-4s|  \n'
               '__| %(levelname)-10s              %(name)48s |__\n'
               '\n'
               '%(message)s')

    flags = set(args)

    so_sheriffs, write_sherrifs = get_badge_data_and_write_function(
        badge_id=3109, filename='sherrif')
    so_constituents, write_constituents = get_badge_data_and_write_function(
        badge_id=1974, filename='constituent')
    so_caucus, write_caucus = get_badge_data_and_write_function(
        badge_id=1973, filename='caucus')

    if not flags.intersection(['-n', '--no-update']):
        so_sheriffs.update()
        write_sherrifs()

        so_constituents.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))

        so_caucus.update(stop_on_existing=bool(
            flags.intersection(['-x', '--stop-on-existing'])))

    logger.info("Grouping constituents by election...")
    constituents_by_reason = so_constituents.by_reason()
    logger.info("...grouped constituents by election.")

    logger.info("Grouping caucuses by election...")
    caucus_by_reason = so_caucus.by_reason()
    logger.info("...grouped caucuses by election.")

    assert len(constituents_by_reason) == len(caucus_by_reason)

    latest_constituents = constituents_by_reason[
        'for an <a href="/election/6">election</a>']
    latest_caucus = caucus_by_reason[
        'for an <a href="/election/6">election</a>']

    chunk_duration = 15 * 60

    election_start_timestamp = min([
        latest_constituents[0].timestamp, latest_caucus[0].timestamp])
    election_end_timestamp = max([
        latest_constituents[-1].timestamp, latest_caucus[-1].timestamp])
    election_chunks = int(
        1 + math.floor(election_end_timestamp - election_start_timestamp) /
        chunk_duration)

    logger.info("Grouping constituent badges into chunks.")

    constituents_by_chunk = [0 for _ in range(election_chunks)]

    for badge in latest_constituents:
        constituents_by_chunk[
            int(math.floor(
                (badge.timestamp - election_start_timestamp) /
                chunk_duration))] += 1

    logger.info("Grouping caucus badges into chunks.")

    caucus_by_chunk = [0 for _ in range(election_chunks)]

    for badge in latest_caucus:
        caucus_by_chunk[
            int(math.floor(
                (badge.timestamp - election_start_timestamp) /
                chunk_duration))] += 1

    logger.info("Generating graph.")

    chart = pygal.Line(
        title="Latest Election Activity by chunk",
        y_title="Users",
        x_title="Quarter-hours",
        show_dots=False,
        range=(0, 512),
        width=1024,
        height=768,
        value_formatter=lambda n: str(int(n)),
        legend_at_bottom=True,
        style=pygal.style.LightStyle
    )
    chart.add('constituents', constituents_by_chunk)
    chart.add('caucus', [n_constituents
                         for n_caucus, n_constituents
                         in zip(caucus_by_chunk, constituents_by_chunk)])

    chart.render_to_file('data/latest-election.svg')
    logger.info("wrote data/latest-election.svg")

    if not flags.intersection(['-n', '--no-update']):
        write_constituents()
        write_caucus()

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

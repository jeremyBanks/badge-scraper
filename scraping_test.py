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



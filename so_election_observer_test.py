#!/usr/bin/env python3
import logging

import pytest

import so_election_observer


logger = logging.getLogger(__name__)


def test_get_publicist_and_have_publicist():
    so_publicist, _ = (
        so_election_observer.get_badge_data_and_write_function(
            badge_id=262, filename='publicist', require_file=True))

    assert any(badge.user_id == 1114 for badge in so_publicist)

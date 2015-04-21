Scraping badge data from Stack Exchange and generating some graphs.

[![Status on Travis CI](https://travis-ci.org/jeremybanks/badge-scraper.svg)](https://travis-ci.org/jeremybanks/badge-scraper)

## Graphs

### Latest Election

![](https://rawgit.com/jeremybanks/badge-scraper/master/data/latest-election-constituents.svg)

![](https://rawgit.com/jeremybanks/badge-scraper/master/data/latest-election.svg)

![](https://rawgit.com/jeremybanks/badge-scraper/master/data/latest-election-sums.svg)

## Run

It's a slow.

    pip3 install -r requirements.txt &&
    python3 -m pytest &&
    ./so_election_observer.py -x

## Flags

`-x`, `--stop-on-existing`: Stop scraping for new instances of a badges once an already-known instance has been encountered.

`-n`, `--no-update`: Don't scrape any new data, just use what you already have.

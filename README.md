Crudely scraping badge data from Stack Exchange, and maybe generating some graphs.

[![Status on Travis CI](https://travis-ci.org/jeremybanks/badge-scraper.svg)](https://travis-ci.org/jeremybanks/badge-scraper.svg)

## Run

It's a bit slow.

    pip3 install -r requirements.txt &&
    python3 -m pytest &&
    ./so_election_observer.py -x

![](https://raw.githubusercontent.com/jeremybanks/badge-scraper/master/data/latest-election.svg)

![](https://raw.githubusercontent.com/jeremybanks/badge-scraper/master/data/latest-election-sums.svg)

## Flags

`-x`, `--stop-on-existing`: Stop scraping for new instances of a badges once an already-known instance has been encountered.

`-n`, `--no-update`: Don't scrape any new data, just use what you already have.

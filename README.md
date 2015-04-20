Crudely scraping badge data from Stack Exchange, and maybe generating some graphs.

[![Status on Travis CI](https://travis-ci.org/jeremybanks/badge-scraper.svg)](https://travis-ci.org/jeremybanks/badge-scraper.svg)

## Run

    pip3 install -r requirements.txt &&
    python3 -m pytest &&
    ./so_election_observer.py -x

## Flags

`-x', '--stop-on-existing`: stops scraping for new badges once a known
badge has been seen again. This is safe if you have valid data.

`-n`, `--no-update`: doesn't scrape any new data, just uses what you
already have.

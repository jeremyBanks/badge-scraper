Scraping badge data from Stack Exchange and generating some graphs.

[![Status on Travis CI](https://travis-ci.org/jeremybanks/badge-scraper.svg)](https://travis-ci.org/jeremybanks/badge-scraper)

## Graphs

### Election Activity

![](https://rawgit.com/jeremybanks/badge-scraper/master/images/election-5-6-both-cumulative.svg)  
![](https://rawgit.com/jeremybanks/badge-scraper/master/images/election-stackoverflow.com-6-both-per-hour.svg)  
![](https://rawgit.com/jeremybanks/badge-scraper/master/images/election-stackoverflow.com-5-both-per-hour.svg)  
![](https://rawgit.com/jeremybanks/badge-scraper/master/images/math-comparison-both-cumulative.svg)

## Run

    pip3 install -r requirements.txt &&
    python3 -m pytest &&
    ./election_observer.py

Writing updated data back to disk is very slow.

## Flags

`-n`, `--no-update`: Don't fetch any new/updated data, just use what you already have.

`-m`, `--no-write`: Don't write any new/updated data.

`-e`, `--forever`: Repeat forever, with some delay.

## Needed Improvements

- We shouldn't remove the existing data files until we finish writing the updated ones. Interrupting a write can currently cause corruption.

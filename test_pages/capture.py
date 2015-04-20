#!/usr/bin/env python
import logging
import re
import sys
import time
import hashlib

import requests


logger = logging.getLogger(__name__)


def main(path):
    logging.basicConfig(level=logging.DEBUG)

    url_base = 'http://stackoverflow.com/'
    url = url_base + path

    logger.debug("url == {!r}".format(url))

    response = requests.get(url)

    sha256_hex = hashlib.sha256(response.content).hexdigest()

    module_name = (
        'so_' + re.sub(r'[^A-Za-z0-9_]+', '_', path) + '_x' +
        sha256_hex[:4])

    with open(module_name + '.py', 'wt') as f:
        f.write('url = {!r} \n'.format(url))
        f.write('path = {!r} \n'.format(path))
        f.write('client_timestamp = {!r}\n'.format(time.gmtime()))
        f.write('sha256_hex = {!r} \n'.format(sha256_hex))
        f.write('text = {!r} \n'.format(response.text))
        f.write('content = {!r} \n'.format(response.content))

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

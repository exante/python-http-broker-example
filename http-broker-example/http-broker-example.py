#!/usr/bin/env python
#
# Copyright (c) 2017 EXANTE
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#

import argparse
import logging
import os
from libs import grid_broker_worker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple grid broker')
    parser.add_argument('application', help='application ID')
    parser.add_argument('account', help='account ID')
    parser.add_argument('-e', '--environment', default='demo',
                        help='environment. Default is demo')
    parser.add_argument('-g', '--grid', type=float, default=0.01,
                        help='grid size. Default is 0.01')
    parser.add_argument('-i', '--instrument', default='EUR/USD.E.FX',
                        help='instrument ID. Default EUR/USD.E.FX')
    parser.add_argument('--interval', type=int, default=10,
                        help='interval to check orders, sec. Default is 10')
    parser.add_argument('-q', '--quantity', type=int, default=1,
                        help='quantity to trade. Default is 1',)
    parser.add_argument('-t', '--token',
                        help='user token, TOKEN env will be read if empty')
    parser.add_argument('--log', help='log file')
    parser.add_argument('--log-format', help='log formating',
                        default='%(asctime)s : \
%(levelname)s : %(funcName)s : %(message)s')
    parser.add_argument('--log-level', default='warning',
                        help='log level. Default is warning',
                        choices=['debug', 'info', 'warning', 'error',
                                 'critical'])
    args = parser.parse_args()

    # apply logging settings
    loglevel = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        filename=args.log, format=args.log_format, level=loglevel)

    try:
        token = args.token if args.token else os.environ['TOKEN']
    except KeyError:
        logging.warning('Cannot find token')
        exit(1)
    url = 'https://api-{}.exante.eu'.format(args.environment)

    # init
    worker = grid_broker_worker.GridBrokerWorker(args.account, args.interval,
                                                 url, args.application, token)
    worker.run(args.instrument, args.quantity, args.grid)

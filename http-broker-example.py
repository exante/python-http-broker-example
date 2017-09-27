#!/usr/bin/env python

import argparse
import logging
import os
import grid_broker_worker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple grid broker')
    parser.add_argument('application', help='application ID')
    parser.add_argument('account', help='account ID')
    parser.add_argument('-e', '--environment', help='environment', default='demo')
    parser.add_argument('-g', '--grid', help='grid size', type=float, default=0.01)
    parser.add_argument('-i', '--instrument', help='instrument ID', default='EUR/USD.E.FX')
    parser.add_argument('--interval', help='interval to check orders, seconds', type=int, default=10)
    parser.add_argument('-q', '--quantity', help='quantity to trade', type=int, default=1)
    parser.add_argument('-t', '--token', help='user token, will be read from TOKEN env if empty')
    parser.add_argument('--log', help='log file. Default is None')
    parser.add_argument('--log-format', help='log formating',
                        default='%(asctime)s : %(levelname)s : %(funcName)s : %(message)s')
    parser.add_argument('--log-level', help='log level. Default is warning', default='warning',
                        choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = parser.parse_args()

    # apply logging settings
    loglevel = getattr(logging, args.log_level.upper())
    logging.basicConfig(filename=args.log, format=args.log_format, level=loglevel)

    try:
        token = args.token if args.token else os.environ['TOKEN']
    except KeyError:
        logging.warning('Cannot find token')
        exit(1)
    url = 'http://api-{}.exante.eu'.format(args.environment)

    # init
    worker = grid_broker_worker.GridBrokerWorker(args.account, args.interval,
                                                 url, args.application, token)
    worker.run(args.instrument, args.quantity, args.grid)

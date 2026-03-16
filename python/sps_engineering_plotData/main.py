#!/usr/bin/env python
# encoding: utf-8

import argparse
import logging
import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication
from sps_engineering_plotData.mainwindow import MainWindow


def setup_logging():
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    log_path = f'/data/logs/plotdata-{timestamp}.log'

    fmt = logging.Formatter('%(asctime)s  %(levelname)-8s  %(name)s: %(message)s',
                            datefmt='%Y-%m-%dT%H:%M:%S')

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def main():
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='db-ics', type=str, nargs='?',
                        help='PostgreSQL host')
    parser.add_argument('--port', default=5432, type=int, nargs='?',
                        help='PostgreSQL port')
    parser.add_argument('--password', default=None, type=str, nargs='?',
                        help='PostgreSQL password')
    parser.add_argument('--dbname', default='archiver', type=str, nargs='?',
                        help='Database name')
    parser.add_argument('--fontsize', default=8, type=int, nargs='?',
                        help='application font size')

    args = parser.parse_args()
    app = QApplication(sys.argv)

    # setting user fontsize
    font = app.font()
    font.setPointSize(args.fontsize)
    app.setFont(font)

    w = MainWindow(**vars(args))
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

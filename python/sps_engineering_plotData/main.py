#!/usr/bin/env python
# encoding: utf-8

import argparse
import sys

from PyQt5.QtWidgets import QApplication
from sps_engineering_plotData.mainwindow import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='db-ics', type=str, nargs='?',
                        help='PostgreSQL host')
    parser.add_argument('--port', default=5432, type=int, nargs='?',
                        help='PostgreSQL port')
    parser.add_argument('--password', default=None, type=str, nargs='?',
                        help='PostgreSQL password')
    parser.add_argument('--dbname', default='archiver', type=str, nargs='?',
                        help='Database name')
    parser.add_argument('--fontsize', default=9, type=int, nargs='?',
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

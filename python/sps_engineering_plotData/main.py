#!/usr/bin/env python
# encoding: utf-8

import argparse
import sys

from PyQt5.QtWidgets import QApplication
from sps_engineering_plotData.mainwindow import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=None, type=str, nargs='?',
                        help='PostgreSQL host')
    parser.add_argument('--port', default=None, type=int, nargs='?',
                        help='PostgreSQL port')
    parser.add_argument('--password', default=None, type=str, nargs='?',
                        help='PostgreSQL password')
    parser.add_argument('--dbname', default=None, type=str, nargs='?',
                        help='Database name')
    args = parser.parse_args()
    app = QApplication(sys.argv)

    w = MainWindow(**vars(args))
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

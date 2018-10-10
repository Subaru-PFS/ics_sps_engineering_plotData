#!/usr/bin/env python
# encoding: utf-8

import argparse
import sys

from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='tron', type=str, nargs='?',
                        help='PostgreSQL host')
    parser.add_argument('--port', default=5432, type=int, nargs='?',
                        help='PostgreSQL port')
    parser.add_argument('--password', default='', type=str, nargs='?',
                        help='PostgreSQL password')
    args = parser.parse_args()
    app = QApplication(sys.argv)

    w = MainWindow(args.host, args.port, args.password)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

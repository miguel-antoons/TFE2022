#! /usr/bin/env python3
import argparse
import subprocess
import os
from datetime import datetime, timedelta


class psdError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Unknown error during the program execution.'
        super(psdError, self).__init__(msg)


def main(args):
    program_name = '/bira-iasb/projects/BRAMS/bin/brams'
    program_command = 'get'
    start_date = datetime.strptime(args.start_date[0], '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    stations = f"{' '.join([station for station in args.stations])}"

    if abs((end_date - start_date).days) > 367:
        raise psdError('Difference between start date and end date'
                       ' cannot be greater than 366 days')

    while start_date < end_date:
        start_date_5min = start_date + timedelta(minutes=5)
        time_interval = (
            f"{start_date.strftime('%Y-%m-%dT%H:%M')}/"
            f"{start_date_5min.strftime('%H:%M')}"
        )

        subprocess.run(
            [
                program_name,
                program_command,
                time_interval,
                stations,
                os.getcwd()
            ],
            check=True
        )

        start_date += timedelta(hours=1)


def arguments():
    parser = argparse.ArgumentParser(
        description='Detect high noise variations in BRAMS .wav files'
    )
    parser.add_argument(
        'start_date',
        metavar='START DATE',
        help="""
            begin date of the files to fetch. This date must be in the
            YYY-MM-DD format.
        """,
        nargs=1
    )
    parser.add_argument(
        'end_date',
        metavar='END DATE',
        help="""
            end date of the files to fetch. This date must be in the
            YYY-MM-DD format.
        """,
        nargs='?',
        default=None
    )
    parser.add_argument(
        'stations',
        metavar='STATIONS',
        help="""
            list with the codes of the stations to detect noise variations on.
        """,
        nargs='+'
    )
    parser.add_argument(
        '-i', '--interval',
        help='interval in minutes to take files. Default is 60.',
        default=60,
        type=int,
        nargs=1
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main(arguments())

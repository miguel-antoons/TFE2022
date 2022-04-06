#! /usr/bin/env python3
import argparse


def main():
    ...


def arguments():
    parser = argparse.ArgumentParser(
        description='Detect high noise variations in BRAMS .wav files'
    )
    parser.add_argument(
        'start_date',
        metavar='START DATE',
        help='time to start detecting high noise variationsin YYYY-MM-DD '
                'format. Note that this date cannot be in the future. '
                'This script can\'t detect high '
                'noise variation in real time...yet.',
        nargs=1
    )
    parser.add_argument(
        'end_date',
        metavar='END DATE',
        help='time to stop detecting high noise variationsin YYYY-MM-DD format'
                '. Note that this date cannot be in the future. This script '
                'can\'t detect high '
                'noise variation in real time...yet.',
        nargs='?',
        default=None
    )
    parser.add_argument(
        'stations',
        metavar='STATIONS',
        help='name of the stations to detect noise variations on.',
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
    args = arguments()
    print(args)
    main()

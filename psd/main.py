#! /usr/bin/env python3
import argparse
from noise_psd import SSB_noise
from brams.brams_wav_2 import BramsWavFile
import os
from datetime import datetime
import mysql.connector


default_dir = 'recordings/BEHAAC'


class psdError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Unknown error during the program execution.'
        super(psdError, self).__init__(msg)


def get_cursor_connection():
    db = mysql.connector.connect(
        host=os.getenv('HOST'),
        user=os.getenv('USER'),
        password=os.getenv('PASSWORD'),
        database=os.getenv('DATABASE')
    )

    return db, db.cursor


def close_connection(connection, cursor):
    connection.close()
    cursor.close()


def insert_into_db(psd_data):
    connection, cursor = get_cursor_connection()


def get_station_ids(stations):
    connection, cursor = get_cursor_connection()

    sql_query = (
        "SELECT system.id, location_id"
        "FROM system"
        "JOIN location on location.id = location_id"
        "WHERE location_code = %d"
    )

    cursor.executemany(sql_query, stations)
    for (id, loc_id) in cursor:
        print(id, loc_id)


def main(args):
    start_date = datetime.strptime(args.start_date[0], '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    stations = args.stations
    get_station_ids(stations)

    directory = os.path.join(os.getcwd(), args.directory)
    directory_content = os.listdir(directory)
    asked_files = []

    for filename in directory_content:
        split_filename = filename.split('_')
        # get date and time of the file
        file_date = datetime.strptime(
            f'{split_filename[2]} {split_filename[3]}',
            '%Y%m%d %H%M'
        )

        # if the file is a file requested by the user
        if (
            file_date >= start_date
            and file_date <= end_date
            and split_filename[4] in stations
        ):
            asked_files.append({
                "filename": filename,
                "time": file_date.strftime('%Y-%m-%d %H:%M')
            })

    for file in asked_files:
        # print(i)
        file_path = os.path.join(directory, file['filename'])

        # check the path is a file
        if os.path.isfile(file_path):
            f = BramsWavFile(file_path)
            power, psd, rms = SSB_noise(f)
            file["psd"] = psd

    print(asked_files)


def arguments():
    parser = argparse.ArgumentParser(
        description='Detect high noise variations in BRAMS .wav files'
    )
    parser.add_argument(
        'start_date',
        metavar='START DATE',
        help="""
            time to start detecting high noise variations in YYYY-MM-DD format.
            Note that this date cannot be in the future. This script can\'t
            detect high noise variation in real time...yet.
        """,
        nargs=1
    )
    parser.add_argument(
        'end_date',
        metavar='END DATE',
        help="""
            time to stop detecting high noise variations in YYYY-MM-DD format.
            Note that this date cannot be in the future. This script can\'t
            detect high noise variation in real time...yet.
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
    parser.add_argument(
        '-d', '--directory',
        help=f"""
            Location of the .wav file to find the noise power spectral density
            of. this value defaults to {default_dir}.
        """,
        default=default_dir,
        type=str,
        nargs=1
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = arguments()
    main(args)

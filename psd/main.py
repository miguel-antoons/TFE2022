#! /usr/bin/env python3
import argparse
import mysql.connector
import os
import matplotlib.pyplot as plt

from brams.brams_wav_2 import BramsWavFile
from packages.variations import detect_noise_decrease
from noise_psd import SSB_noise
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm


default_dir = 'recordings/'


class psdError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Unknown error during the program execution.'
        super(psdError, self).__init__(msg)


def get_cursor_connection():
    load_dotenv()
    db = mysql.connector.connect(
        host=os.getenv('HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('PASSWORD'),
        database=os.getenv('DATABASE')
    )

    return db, db.cursor()


def close_connection(connection, cursor):
    cursor.close()
    connection.close()


def insert_into_db(psd_data):
    connection, cursor = get_cursor_connection()
    print('Saving values in the database...')

    sql_query = (
        "UPDATE file "
        "SET noise = %(psd)s "
        "WHERE "
        "system_id = %(system_id)s "
        "AND start = %(time)s"
    )

    try:
        cursor.executemany(sql_query, psd_data)
        connection.commit()
    except mysql.connector.Error as e:
        connection.rollback()
        print(e)

    close_connection(connection, cursor)


def get_station_ids(stations):
    arguments = ['%s' for i in range(len(stations))]
    ids = {}
    connection, cursor = get_cursor_connection()

    # get system_id for each location and antenna
    sql_query = (
        "SELECT system.id, location_code, antenna\n"
        "FROM `system`, location\n"
        "WHERE location.id = system.location_id AND location_code in (%s);"
        % ', '.join(arguments)
    )

    cursor.execute(sql_query, tuple(stations))

    print('Structuring data received from the database...')
    # structure the system id's first by location code and then by antenna
    for (sys_id, loc_code, antenna) in tqdm(cursor):
        if loc_code not in ids:
            ids[loc_code] = {}

        ids[loc_code][str(antenna)] = sys_id

    close_connection(connection, cursor)

    return ids


def main(args):
    start_date = datetime.strptime(args.start_date[0], '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    stations = args.stations
    station_ids = get_station_ids(stations)

    directory = os.path.join(os.getcwd(), args.directory, args.stations[0])
    directory_content = os.listdir(directory)
    asked_files = []

    print('Retrieving relevant files...')
    # check which files are relevant and store them in an array
    for filename in tqdm(directory_content):
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
                "time": file_date.strftime('%Y-%m-%d %H:%M'),
                "system_id": (
                    station_ids
                    [split_filename[4]]
                    [str(int(
                        split_filename[5]
                        .replace('SYS', '')
                        .replace('.wav', '')
                    ))]
                ),
            })

    print('Calculating psd for each file...')
    i = 0
    x = []
    y = []
    # calculating psd for each file
    for file in tqdm(asked_files):
        # print(i)
        file_path = os.path.join(directory, file['filename'])

        # check the path is a file
        if os.path.isfile(file_path):
            i += 1
            x.append(i)
            f = BramsWavFile(file_path)
            psd = SSB_noise(f)
            y.append(psd)
            file["psd"] = psd
            # detect_noise_decrease(x, y, i)

    plt.plot(x, y)
    plt.show()
    insert_into_db(asked_files)


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
    # args = argparse.Namespace(
    #     start_date=['2021-07-01'],
    #     end_date='2021-08-31',
    #     stations=['BEHAAC'],
    #     directory=default_dir,
    # )
    args = argparse.Namespace(
        start_date=['2020-06-01'],
        end_date='2020-09-30',
        stations=['BEOOSE'],
        directory=default_dir,
    )
    # args = arguments()
    main(args)
    # test_methods(args)

#! /usr/bin/env python3
import argparse
import json
import os
# import matplotlib.pyplot as plt

from modules.brams_wav_2 import BramsWavFile
from modules.psd.variations import detect_noise_decrease, detect_noise_increase
from modules.psd.database import get_station_ids, insert_noise
from modules.psd.psd import SSB_noise
from datetime import datetime, timedelta
from tqdm import tqdm


default_dir = 'recordings/'
# default_dir = /bira-iasb/data/GROUNDBASED/BRAMS


class psdError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Unknown error during the program execution.'
        super(psdError, self).__init__(msg)


def main(args):
    if args.start_date is not None:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        stations = args.stations

        asked_files = get_asked_files(
            start_date,
            end_date,
            stations,
            args.directory
        )

    print('Calculating psd for each file...')
    # ! below arrays have to change to dictionnaries in order to support multiple stations
    noise_memory = {}
    # calculating psd for each file
    for file in tqdm(asked_files):
        if noise_memory[file['station_code']] is None:
            noise_memory[file['station_code']] = {
                "i": 0,
                "x": [],
                "Y": []
            }
        f = BramsWavFile(file['filename'])
        psd = SSB_noise(f)

        noise_memory[file['station_code']]['i'] += 1
        noise_memory[file['station_code']]['x'].append(i)
        noise_memory[file['station_code']]['y'].append(psd)

        file["psd"] = float(psd)
        if noise_memory[file['station_code']]['i'] > 1:
            detect_noise_increase(
                noise_memory
                [file['station_code']]
                ['y']
                [noise_memory[file['station_code']]['i'] - 2],
                psd,
                noise_memory[file['station_code']]['i']
            )
        detect_noise_decrease(
            noise_memory[file['station_code']]['x'],
            noise_memory[file['station_code']]['y'],
            noise_memory[file['station_code']]['i']
        )

    # plt.plot(x, y)
    # plt.show()
    insert_noise(asked_files)


def get_asked_files(start_date, end_date, stations, parent_directory):
    station_ids = get_station_ids(stations)

    directory = os.path.join(os.getcwd(), parent_directory, args.stations[0])
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
            file_path = os.path.join(directory, filename)
            # check the path is a file
            if os.path.isfile(file_path):
                asked_files.append({
                    "station_code": split_filename[4],
                    "filename": file_path,
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

    return asked_files


def verify_archive_date(start_date, dir_content):
    if str(start_date.year) not in dir_content:
        print('No new files were archived.')
        return False

    directory = os.path.join(default_dir, str(start_date.year))
    dir_content = os.listdir(directory)

    if str(start_date.month) not in dir_content:
        print('No new files were archived.')
        return False

    directory = os.path.join(directory, str(start_date.month))
    dir_content = os.listdir(directory)

    if str(start_date.day) not in dir_content:
        print('No new files were archived.')
        return False

    return os.listdir(os.path.join(directory, str(start_date.day)))


def get_archived_files():
    data = None
    with open('program_data.json') as f:
        data = json.load(f)

    # if no file was found
    if data is None:
        start_date = datetime.now() - timedelta(1)
        print(
            'No data file found, setting default date (yesterday)'
        )
    else:
        start_date = (
            datetime.strptime(data['previous_date'], '%Y-%m-%d') + timedelta(1)
        )

    while (
        dir_content := verify_archive_date(start_date, os.listdir(default_dir))
    ):
        for filename in tqdm(dir_content):
            split_filename = filename.split('_')
            # get date and time of the file
            file_date = datetime.strptime(
                f'{split_filename[2]} {split_filename[3]}',
                '%Y%m%d %H%M'
            )


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
        nargs='?',
        default=None
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
    args = argparse.Namespace(
        start_date='2021-07-01',
        end_date='2021-08-31',
        stations=['BEHAAC'],
        directory=default_dir,
    )
    # args = argparse.Namespace(
    #     start_date='2020-06-01',
    #     end_date='2020-09-30',
    #     stations=['BEOOSE'],
    #     directory=default_dir,
    # )
    # args = arguments()
    main(args)
    # test_methods(args)

#! /usr/bin/env python3
import argparse
import json
import os
import modules.database.file as f
import modules.database.system as sys
import modules.psd.variations as variations
import modules.psd.psd as psd
# import matplotlib.pyplot as plt

from modules.brams_wav_2 import BramsWavFile
from datetime import datetime, timedelta
from tqdm import tqdm


default_dir = 'recordings/'
# default_dir = /bira-iasb/data/GROUNDBASED/BRAMS/


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
        last_date = None
    else:
        asked_files, last_date = get_archived_files()

    noise_memory = {}
    print('Calculating psd for each file...')
    # calculating psd for each file
    # for file in tqdm(asked_files):
    for file in asked_files:
        print('\n-----------------------------------------------------')
        print(file['station_code'])
        # if it is the first (during program execution) time that psd will be
        # calculated for this station
        if file['system_id'] not in noise_memory.keys():
            # get the preious psd values from the database
            previous_psd = f.get_previous_noise_psd(
                [file['system_id']],
                False
            )
            previous_calibrator = f.get_previous_calibrator_psd(
                [file['system_id']],
                False
            )

            # check if there are any psd values received from the database
            if file['system_id'] not in previous_psd.keys():
                # if there are no values, set an empty array as previous psd
                # values
                previous_psd[file['system_id']] = []

            # check if there were any calibrator psd values for this station
            if file['system_id'] not in previous_calibrator.keys():
                # if non values were found, default to None
                previous_calibrator[file['system_id']] = None

            # add a dict to the noise_memory variable representing psd values
            # for the current station
            noise_memory[file['system_id']] = {
                "i": len(previous_psd[file['system_id']]) - 1,
                "x": [i for i in range(len(previous_psd[file['system_id']]))],
                "y": previous_psd[file['system_id']],
                "previous_calibrator": previous_calibrator[file['system_id']],
                "previous_f": None
            }

        # read the wav file and calculate the noise and callibrator psd value
        wav = BramsWavFile(file['filename'])
        noise_psd = psd.get_noise_psd(wav)
        calibrator_psd, calibrator_f = psd.get_calibrator_psd(wav)

        # increment the counter, append an x value and apprend the psd value
        # to the y array
        noise_memory[file['system_id']]['i'] += 1
        noise_memory[file['system_id']]['x'].append(
            noise_memory[file['system_id']]['i'])
        noise_memory[file['system_id']]['y'].append(noise_psd)

        # if the length exceeds 150
        if len(noise_memory[file['system_id']]['x']) > 150:
            # trim the y and x array since we need no more than 150 values
            noise_memory[file['system_id']]['x'] = (
                noise_memory
                [file['system_id']]
                ['x']
                [-150:]
            )
            noise_memory[file['system_id']]['y'] = (
                noise_memory
                [file['system_id']]
                ['y']
                [-150:]
            )

        # store the psd value in the file dict
        file["noise_psd"] = float(noise_psd)
        if calibrator_psd is not None:
            file["calibrator_psd"] = float(calibrator_psd)
        else:
            file["calibrator_psd"] = calibrator_psd

        variations.detect_calibrator_variations(
            noise_memory[file['system_id']]['previous_calibrator'],
            calibrator_psd
        )

        # if there is a value to compare to
        if noise_memory[file['system_id']]['i'] > 1:
            # compare the current psd to the previous one in order
            # to detect high noise increases
            variations.detect_noise_increase(
                noise_memory
                [file['system_id']]
                ['y']
                [noise_memory[file['system_id']]['i'] - 2],
                noise_psd,
                noise_memory[file['system_id']]['i']
            )

        # finally, detect if there is a noise decrease
        variations.detect_noise_decrease(
            noise_memory[file['system_id']]['x'],
            noise_memory[file['system_id']]['y'],
            noise_memory[file['system_id']]['i']
        )

        noise_memory[file['system_id']]['previous_calibrator'] = (
            calibrator_psd
        )
        noise_memory[file['system_id']]['previous_f'] = calibrator_f

    # plt.plot(x, y)
    # plt.show()
    # insert the noise psd values into the database
    if (
        f.insert_noise(asked_files)
        and f.insert_calibrator(asked_files)
        and last_date is not None
    ):
        with open('program_data.json', 'w') as json_file:
            json.dump(
                {
                    "previous_date": last_date
                },
                json_file
            )


def get_asked_files(start_date, end_date, stations, parent_directory):
    station_ids = sys.get_station_ids(stations, False)

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
                    "datetime": file_date,
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

    # return the list of new files ordered by their date
    return sorted(asked_files, key=lambda d: d['datetime'])


def verify_archive_date(start_date):
    dir_content = os.listdir(default_dir)

    if (year := start_date.strftime('%Y')) not in dir_content:
        return False

    directory = os.path.join(default_dir, year)
    dir_content = os.listdir(directory)

    if (month := start_date.strftime('%m')) not in dir_content:
        return False

    directory = os.path.join(directory, month)
    dir_content = os.listdir(directory)

    if (day := start_date.strftime('%d')) not in dir_content:
        return False

    return {
        "path": os.path.join(directory, day),
        "content": os.listdir(os.path.join(directory, day))
    }


def get_archived_files():
    try:
        with open('program_data.json') as f:
            data = json.load(f)
    except FileNotFoundError as e:
        # logging.warning(e)
        data = None

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

    files_to_archive = []
    station_ids = sys.get_station_ids()

    # while a new directory with new files is found
    while (directory := verify_archive_date(start_date)):
        for filename in tqdm(directory['content']):
            split_filename = filename.split('_')
            # get date and time of the file
            file_date = datetime.strptime(
                f'{split_filename[2]} {split_filename[3]}',
                '%Y%m%d %H%M'
            )
            file_path = os.path.join(directory['path'], filename)

            # check the path is a file
            if os.path.isfile(file_path):
                files_to_archive.append({
                    "station_code": split_filename[4],
                    "filename": file_path,
                    "time": file_date.strftime('%Y-%m-%d %H:%M'),
                    "datetime": file_date,
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

        # increase the date by 1 day
        start_date += timedelta(1)
    else:
        print('All new archived files were retrieved.')

    return (
        sorted(files_to_archive, key=lambda d: d['datetime']),
        start_date.strftime('%Y-%m-%d')
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
        nargs='*',
        default=None
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
    #     start_date='2021-07-01',
    #     end_date='2021-08-31',
    #     stations=['BEHAAC'],
    #     directory=default_dir,
    # )
    # args = argparse.Namespace(
    #     start_date='2020-06-01',
    #     end_date='2020-09-30',
    #     stations=['BEOOSE'],
    #     directory=default_dir,
    # )
    args = arguments()
    main(args)
    # test_methods(args)

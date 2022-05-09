#! /usr/bin/env python3
import argparse
import json
import os
import modules.database.system as sys
import modules.psd.variations as variations
import modules.psd.psd as psd
import matplotlib.pyplot as plt

from modules.brams_wav_2 import BramsWavFile
from datetime import datetime, timedelta
from tqdm import tqdm

# 1. assume that the files are structured by YEAR/MONTH/DATE by default
# 2. don't forget to take into account the interval
# 3. create graph and png from that graph (with matplotlib)


default_dir = 'recordings/'
# default_dir = '/bira-iasb/data/GROUNDBASED/BRAMS/'


def main(args):
    stations = args.stations
    # if a directory is given
    if args.directory is not None:
        # get all the files in the directory that are within a date interval
        asked_files = get_asked_files(
            args.start_date,
            args.end_date,
            stations,
            args.directory
        )
        last_date = None
    # if no directory is given
    else:
        # get files files from the archive that are within a date interval
        asked_files, last_date = get_archived_files(
            args.interval,
            stations,
            args.start_date,
            args.end_date,
        )

    noise_memory = {}
    print('Calculating psd for each file...')
    # calculating psd for each file
    for file in tqdm(asked_files):
        sys_id = file['system_id']
        # for file in asked_files:
        # if it is the first (during program execution) time that psd will be
        # calculated for this station
        if sys_id not in noise_memory.keys():
            # if there are no values, set an empty array as previous psd
            # values
            previous_psd = {sys_id: []}

            # if non values were found, default to None
            previous_calibrator = {sys_id: None}

            # add a dict to the noise_memory variable representing psd values
            # for the current station
            noise_memory[sys_id] = {
                "i": len(previous_psd[sys_id]) - 1,
                "x": [i for i in range(len(previous_psd[sys_id]))],
                "n_y": previous_psd[sys_id],
                "c_y": [],
                "previous_calibrator": previous_calibrator[sys_id],
                "previous_f": None,
                "warnings": {
                    "noise": {
                        "desc": [],
                        "asc": [],
                    },
                    "calibrator": [],
                },
            }

        # read the wav file and calculate the noise and callibrator psd value
        wav = BramsWavFile(file['filename'])
        noise_psd = psd.get_noise_psd(wav)
        calibrator_psd, calibrator_f = psd.get_calibrator_psd(wav)

        # increment the counter, append an x value and apprend the psd value
        # to the y array
        noise_memory[sys_id]['i'] += 1
        noise_memory[sys_id]['x'].append(
            noise_memory[sys_id]['i'])
        noise_memory[sys_id]['n_y'].append(noise_psd)
        noise_memory[sys_id]['c_y'].append(calibrator_psd)

        # # if the length exceeds 150
        # if len(noise_memory[file['system_id']]['x']) > 150:
        #     # trim the y and x array since we need no more than 150 values
        #     noise_memory[file['system_id']]['x'] = (
        #         noise_memory
        #         [file['system_id']]
        #         ['x']
        #         [-150:]
        #     )
        #     noise_memory[file['system_id']]['y'] = (
        #         noise_memory
        #         [file['system_id']]
        #         ['y']
        #         [-150:]
        #     )

        # store the psd value in the file dict
        file["noise_psd"] = float(noise_psd)
        if calibrator_psd is not None:
            file["calibrator_psd"] = float(calibrator_psd)
        else:
            file["calibrator_psd"] = calibrator_psd

        if variations.detect_calibrator_variations(
            noise_memory[sys_id]['previous_calibrator'],
            calibrator_psd
        ) > 50:
            noise_memory[sys_id]['warnings']['calibrator'].append(
                noise_memory[sys_id]['i']
            )

        # if there is a value to compare to
        if noise_memory[sys_id]['i'] > 1:
            # compare the current psd to the previous one in order
            # to detect high noise increases
            if variations.detect_noise_increase(
                noise_memory
                [sys_id]
                ['n_y']
                [-1],
                noise_psd,
                noise_memory[sys_id]['i']
            ):
                noise_memory[sys_id]['warnings']['noise']['asc'].append(
                    noise_memory[sys_id]['i']
                )

        # finally, detect if there is a noise decrease
        if variations.detect_noise_decrease(
            noise_memory[sys_id]['x'],
            noise_memory[sys_id]['n_y'],
            noise_memory[sys_id]['i']
        ):
            noise_memory[sys_id]['warnings']['noise']['desc'].append(
                noise_memory[sys_id]['i']
            )

        noise_memory[sys_id]['previous_calibrator'] = (
            calibrator_psd
        )
        noise_memory[sys_id]['previous_f'] = calibrator_f

    with open('test_data.json', 'w') as json_file:
        json.dump(noise_memory, json_file)

    for i, sys_id in enumerate(noise_memory.keys()):
        generate_plot(
            noise_memory[sys_id]['x'],
            noise_memory[sys_id]['n_y'],
            f'{sys_id}_{args.start_date}_{args.end_date}_noise',
            figure_n=i
        )
        generate_plot(
            noise_memory[sys_id]['x'],
            noise_memory[sys_id]['c_y'],
            f'{sys_id}_{args.start_date}_{args.end_date}_calibrator',
            figure_n=i + len(noise_memory.keys())
        )
    # plt.plot(x, y)
    # plt.show()
    # insert the noise psd values into the database
    # if (
    #     f.insert_noise(asked_files)
    #     and f.insert_calibrator(asked_files)
    #     and last_date is not None
    # ):
    #     with open('program_data.json', 'w') as json_file:
    #         json.dump(
    #             {
    #                 "previous_date": last_date
    #             },
    #             json_file
    #         )


def generate_plot(
    x,
    y,
    im_name,
    width=6.4,
    height=4.8,
    figure_n=0,
    dpi=100.0
):
    plt.figure(num=figure_n, figsize=(width, height), dpi=dpi)
    plt.plot(x, y)
    plt.savefig(f'{im_name}.png')


def get_asked_files(start_date, end_date, stations, parent_directory):
    if start_date is None or end_date is None:
        return []

    asked_files = []    # array that will be returned at the end

    # convert it to a date object and get the end-date
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    station_ids = sys.get_station_ids(stations, False)

    # if parent_directory[0] == '/':
    #     directory = parent_directory
    # else:
    #     directory = os.path.join(os.getcwd(), parent_directory)
    # * below line is for testing only use the lines above for production
    directory = os.path.join(os.getcwd(), parent_directory, stations[0])
    directory_content = os.listdir(directory)

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


# ! carefull for exceptions!!
def verify_archive_date(start_date):
    dir_content = os.listdir(default_dir)

    year = start_date.strftime('%Y')
    if year not in dir_content:
        return False

    directory = os.path.join(default_dir, year)
    dir_content = os.listdir(directory)

    month = start_date.strftime('%m')
    if month not in dir_content:
        return False

    directory = os.path.join(directory, month)
    dir_content = os.listdir(directory)

    day = start_date.strftime('%d')
    if day not in dir_content:
        return False

    return {
        "path": os.path.join(directory, day),
        "content": sorted(os.listdir(os.path.join(directory, day)))
    }


def get_archived_files(interval, stations=[], start_date=None, end_date=None):
    if start_date is None:
        try:
            with open('program_data.json') as f:
                data = json.load(f)
        except FileNotFoundError as e:
            print(e)
            # logging.warning(e)
            data = None

        # if no json file was found
        if data is None:
            # set the start_date to yesterday
            start_date = datetime.now() - timedelta(1)
        else:
            start_date = (
                datetime.strptime(data['previous_date'], '%Y-%m-%d')
                + timedelta(1)
            )

        end_date = datetime.now() + timedelta(1)
    else:
        # convert it to a date object and get the end-date
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    files_to_archive = []

    if stations is []:
        station_ids = sys.get_station_ids()
    else:
        station_ids = sys.get_station_ids(stations, False)

    directory = verify_archive_date(start_date)
    # while a new directory with new files is found
    while directory:
        reference_dates = {}

        for filename in tqdm(directory['content']):
            split_filename = filename.split('_')
            if split_filename[4] in station_ids.keys():
                system_id = station_ids[
                    split_filename[4]
                ][
                    str(int(
                        split_filename[5]
                        .replace('SYS', '')
                        .replace('.wav', '')
                    ))
                ]
                # get date and time of the file
                file_date = datetime.strptime(
                    f'{split_filename[2]} {split_filename[3]}',
                    '%Y%m%d %H%M'
                )

                if system_id not in reference_dates.keys():
                    reference_dates[system_id] = file_date
                file_path = os.path.join(directory['path'], filename)

                # check the path is a file and that the interval between the
                # files is respected
                if (
                    os.path.isfile(file_path)
                    and file_date == reference_dates[system_id]
                ):
                    files_to_archive.append({
                        "station_code": split_filename[4],
                        "filename": file_path,
                        "time": file_date.strftime('%Y-%m-%d %H:%M'),
                        "datetime": file_date,
                        "system_id": system_id,
                    })

                    reference_dates[system_id] += timedelta(minutes=interval)

        # increase the date by 1 day
        start_date += timedelta(1)
        directory = verify_archive_date(start_date)
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
        default=[]
    )
    parser.add_argument(
        '-i', '--interval',
        help='interval in minutes to take files. Default is 60.',
        default=60,
        type=int,
        nargs='?'
    )
    parser.add_argument(
        '-d', '--directory',
        help=f"""
            Location of the .wav file to find the noise power spectral density
            of. This value defaults to {default_dir}.
        """,
        default=None,
        type=str,
        nargs='?'
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
    args = arguments()
    main(args)
    # test_methods(args)

    # print(
    #     f.get_file_by_interval(
    #         [2, 53],
    #         {
    #             'start_time': datetime.timestamp(
    #                 datetime.strptime(
    #                     '2022-03-15 11:59:57',
    #                     '%Y-%m-%d %H:%M:%S'
    #                 ).replace(tzinfo=timezone.utc)
    #             ) * 1000000,
    #             'end_time': datetime.timestamp(
    #                 datetime.strptime(
    #                     '2022-03-15 12:00:03',
    #                     '%Y-%m-%d %H:%M:%S'
    #                 ).replace(tzinfo=timezone.utc)
    #             ) * 1000000,
    #         }
    #     )
    # )

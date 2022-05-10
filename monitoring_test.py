#! /usr/bin/env python3
import argparse
import json
import os
import tarfile
import modules.database.system as sys
import modules.psd.variations as variations
import modules.psd.psd as psd
import matplotlib.pyplot as plt

# from modules.brams_wav_2 import BramsWavFile
from modules.brams_wav import BramsError, BramsWavFile, DirectoryNotFoundError
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

# 1. assume that the files are structured by YEAR/MONTH/DATE by default
# 2. don't forget to take into account the interval
# 3. create graph and png from that graph (with matplotlib)


# default_dir = 'recordings/wav/'
default_dir = '/bira-iasb/data/GROUNDBASED/BRAMS/wav/'


def get_dates(start_date: str = None, end_date: str = None):
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
            # ! review below line of code
            start_date = (
                datetime.strptime(data['previous_date'], '%Y-%m-%d')
                + timedelta(1)
            )

        end_date = datetime.now(tz=timezone.utc)
    else:
        # convert it to a date object and get the end-date
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(
            tzinfo=timezone.utc
        )

        now_time = datetime.now(tz=timezone.utc)
        if end_date > now_time:
            end_date = now_time

    start_date = start_date.replace(tzinfo=timezone.utc)
    return start_date, end_date


def main(args):
    files = []
    psd_memory = {}
    stations = args.stations

    # get all the system ids from the requested locations
    if len(stations) == 0:
        systems = sys.get_station_ids()
    else:
        systems = sys.get_station_ids(stations, False)

    if args.directory == default_dir:
        from_archive = True
    else:
        from_archive = False

    # get the start and end date
    start_date, end_date = get_dates(args.start_date, args.end_date)

    interval_delta = timedelta(minutes=args.interval)
    day_delta = timedelta(days=1)
    interval_sec = interval_delta.total_seconds()
    tqdm_day_value = day_delta.total_seconds() / interval_sec

    difference = (
        (end_date - start_date).total_seconds()
        / interval_sec
    )

    for lcode in tqdm(
        systems.keys(),
        position=0,
        desc='Calculating for each station...'
    ):
        for antenna in tqdm(
            systems[lcode].keys(),
            position=1,
            desc='Calculating for each antenna...'
        ):
            sys_id = systems[lcode][antenna]
            requested_date = start_date

            with tqdm(
                total=difference,
                position=2,
                desc='Calculating psd...',
            ) as pbar:
                # perform the monitoring on the whole time interval
                while requested_date < end_date:
                    # if it is the first (during program execution) time that
                    # psd will be calculated for this station
                    if sys_id not in psd_memory.keys():
                        # if there are no values, set an empty array as
                        # previous psd values
                        previous_psd = {sys_id: []}

                        # if non values were found, default to None
                        previous_calibrator = {sys_id: None}

                        # add a dict to the noise_memory variable representing
                        # psd values for the current station
                        psd_memory[sys_id] = {
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

                    sys_psd = psd_memory[sys_id]

                    try:
                        wav = BramsWavFile(
                            requested_date,
                            lcode,
                            f"SYS{antenna.rjust(3, '0')}",
                            parent_directory=args.directory,
                            from_archive=from_archive,
                        )
                    except BramsError:
                        requested_date += interval_delta
                        pbar.update(1)
                        continue
                    except DirectoryNotFoundError:
                        requested_date += day_delta
                        pbar.update(tqdm_day_value)
                        continue

                    noise_psd = psd.get_noise_psd(wav)
                    calibrator_psd, calibrator_f = psd.get_calibrator_psd(wav)

                    # increment the counter, append an x value and apprend the
                    # psd value to the y array
                    sys_psd['i'] += 1
                    sys_psd['x'].append(sys_psd['i'])
                    sys_psd['n_y'].append(noise_psd)
                    sys_psd['c_y'].append(calibrator_psd)

                    if calibrator_psd is None:
                        db_cal_psd = calibrator_psd
                    else:
                        db_cal_psd = float(calibrator_psd)

                    files.append({
                        "system_id": sys_id,
                        "time": wav.date.strftime('%Y-%m-%d %H:%M'),
                        "noise_psd": float(noise_psd),
                        "calibrator_psd": db_cal_psd
                    })

                    if variations.detect_calibrator_variations(
                        sys_psd['previous_calibrator'],
                        calibrator_psd
                    ) > 50:
                        sys_psd['warnings']['calibrator'].append(sys_psd['i'])

                    # if there is a value to compare to
                    if sys_psd['i'] > 1:
                        # compare the current psd to the previous one in order
                        # to detect high noise increases
                        if variations.detect_noise_increase(
                            sys_psd['n_y'][-1],
                            noise_psd,
                            sys_psd['i']
                        ):
                            sys_psd['warnings']['noise']['asc'].append(
                                sys_psd['i']
                            )

                    # finally, detect if there is a noise decrease
                    if variations.detect_noise_decrease(
                        sys_psd['x'],
                        sys_psd['n_y'],
                        sys_psd['i']
                    ):
                        sys_psd['warnings']['noise']['desc'].append(
                            sys_psd['i'])

                    sys_psd['previous_calibrator'] = calibrator_psd
                    sys_psd['previous_f'] = calibrator_f

                    requested_date = wav.date + interval_delta
                    pbar.update(1)

    with open('test_data.json', 'w') as json_file:
        json.dump(psd_memory, json_file)

    for i, sys_id in enumerate(psd_memory.keys()):
        generate_plot(
            psd_memory[sys_id]['x'],
            psd_memory[sys_id]['n_y'],
            f'{sys_id}_{args.start_date}_{args.end_date}_noise',
            figure_n=i
        )
        generate_plot(
            psd_memory[sys_id]['x'],
            psd_memory[sys_id]['c_y'],
            f'{sys_id}_{args.start_date}_{args.end_date}_calibrator',
            figure_n=i + len(psd_memory.keys())
        )


def generate_plot(
    x,
    y,
    im_name,
    width=19.2,
    height=14.4,
    figure_n=0,
    dpi=200.0
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
def verify_archive_date(start_date, end_date=None):
    if end_date is not None and start_date >= end_date:
        return False

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

    directory = verify_archive_date(start_date, end_date)
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
                        .replace('.tar', '')
                    ))
                ]
                file_path = os.path.join(directory['path'], filename)

                # get content of the tar file
                with tarfile.open(file_path) as tar:
                    for member in tar.getmembers():
                        split_filename = member.name.split('_')
                        # get date and time of the file
                        file_date = datetime.strptime(
                            f'{split_filename[2]} {split_filename[3]}',
                            '%Y%m%d %H%M'
                        )

                        if system_id not in reference_dates.keys():
                            reference_dates[system_id] = file_date

                        # check the path is a file and that the interval
                        # between the files is respected
                        if file_date == reference_dates[system_id]:
                            files_to_archive.append({
                                "station_code": split_filename[4],
                                "path": file_path,
                                "filename": member,
                                "time": file_date.strftime('%Y-%m-%d %H:%M'),
                                "datetime": file_date,
                                "system_id": system_id,
                            })

                            reference_dates[system_id] += timedelta(
                                minutes=interval
                            )

        # increase the date by 1 day
        start_date += timedelta(1)
        directory = verify_archive_date(start_date, end_date)
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
        default=default_dir,
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

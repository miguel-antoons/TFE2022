#! /usr/bin/env python3
import argparse
import json
import modules.database.system as sys
import modules.psd.variations as variations
import modules.psd.psd as psd
import matplotlib.pyplot as plt
import numpy as np

# from modules.brams_wav_2 import BramsWavFile
from modules.brams_wav import BramsError, BramsWavFile, DirectoryNotFoundError
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

# 1. assume that the files are structured by YEAR/MONTH/DATE by default
# 2. don't forget to take into account the interval
# 3. create graph and png from that graph (with matplotlib)


# default_dir = 'recordings/wav/'
default_dir = '/bira-iasb/data/GROUNDBASED/BRAMS/wav/'


def read_from_json(args):
    with open('test_data.json') as json_file:
        psd_memory = json.load(json_file)

    for i, sys_id in enumerate(psd_memory.keys()):
        generate_plot(
            psd_memory[sys_id]['x'],
            psd_memory[sys_id]['n_y'],
            f"{psd_memory[sys_id]['title']}_"
            f"{args.start_date}_{args.end_date}_noise",
            figure_n=i,
            title=f"{psd_memory[sys_id]['title']} noise",
            y_title='ADU',
            x_title='date'
        )
        generate_plot(
            psd_memory[sys_id]['x'],
            psd_memory[sys_id]['c_y'],
            f"{psd_memory[sys_id]['title']}_"
            f'{args.start_date}_{args.end_date}_calibrator',
            figure_n=i + len(psd_memory.keys()),
            title=f"{psd_memory[sys_id]['title']} calibrator",
            y_title='ADU',
            x_title='date'
        )


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
            start_date = datetime.strptime(data['previous_date'], '%Y-%m-%d')

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
                            "title": f'{lcode}{antenna}',
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
                            respect_date=True,
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

                    # increment the counter, append an x value and append the
                    # psd value to the y array
                    sys_psd['i'] += 1
                    sys_psd['x'].append(wav.date.strftime('%Y-%m-%d %H:%M'))
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
                        [i for i in range(len(sys_psd['n_y']))],
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

    with open('file_data.json', 'w') as json_file:
        json.dump(files, json_file)

    for i, sys_id in enumerate(psd_memory.keys()):
        generate_plot(
            psd_memory[sys_id]['x'],
            psd_memory[sys_id]['n_y'],
            f"{psd_memory[sys_id]['title']}_"
            f"{args.start_date}_{args.end_date}_noise",
            figure_n=i,
            title=f"{psd_memory[sys_id]['title']} noise",
            y_title='ADU',
            x_title='date'
        )
        generate_plot(
            psd_memory[sys_id]['x'],
            psd_memory[sys_id]['c_y'],
            f"{psd_memory[sys_id]['title']}_"
            f'{args.start_date}_{args.end_date}_calibrator',
            figure_n=i + len(psd_memory.keys()),
            title=f"{psd_memory[sys_id]['title']} calibrator",
            y_title='ADU',
            x_title='date'
        )


def mad(array):
    median = np.median(array)
    return median, np.median(np.abs(array - median))


def generate_plot(
    x,
    y,
    im_name,
    width=26.5,
    height=14.4,
    figure_n=0,
    dpi=350.0,
    title='',
    y_title='',
    x_title='',
):
    y = np.array(y)
    y_median, y_mad = mad(y)
    min_3mad = y_median - (3 * y_mad)
    plus_3mad = y_median + (3 * y_mad)
    lowest_value = np.min(np.abs(y[y > min_3mad]))
    y_min = min_3mad - lowest_value
    y_max = plus_3mad + lowest_value

    plt.figure(num=figure_n, figsize=(width, height), dpi=dpi)
    plt.plot(x, y)
    axis = plt.gca()
    axis.set_ylim([y_min, y_max])
    plt.title(title)
    plt.xlabel(x_title)
    plt.ylabel(y_title)

    if len(x) > 10:
        step = int(len(x) / 10)
    else:
        step = 1
    plt.xticks([i for i in range(0, len(x), step)])
    plt.savefig(f'{im_name}.png')
    plt.close(figure_n)
    print(im_name)


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
    parser.add_argument(
        '-f', '--from-file',
        help="""
            DEV : create graph from json file.
        """,
        action='store_true'
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
    if args.from_file:
        read_from_json(args)
    else:
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

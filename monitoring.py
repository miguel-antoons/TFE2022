#! /usr/bin/env python3
import argparse
import simplejson as json
import modules.database.system as sys
import modules.database.file as f
import modules.psd.variations as variations
import modules.psd.psd as psd
import matplotlib.pyplot as plt
import modules.mail.mail as mail

from modules.brams_wav import BramsError, BramsWavFile, DirectoryNotFoundError
from datetime import datetime, timedelta, timezone
from tqdm import tqdm
from decimal import Decimal
from email.mime.text import MIMEText


default_dir = 'recordings/wav/'
# default_dir = '/bira-iasb/data/GROUNDBASED/BRAMS/wav/'


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


def send_summary(psd_memory):
    summary_text = ""

    for system_id in psd_memory:
        summary_text += (
            f"\n\n----------{psd_memory[system_id]['title']}----------\n"
            "NOISE : \n"
        )

        for warning in psd_memory[system_id]['warnings']['noise']['desc']:
            summary_text += (
                f"There was a significative noise drop at {warning}\n"
            )

        summary_text += "\n"

        for warning in psd_memory[system_id]['warnings']['noise']['asc']:
            summary_text += (
                f" There was a significative noise increase at {warning}\n"
            )

        summary_text += "\nCALIBRATOR : \n"

        for warning in psd_memory[system_id]['warnings']['calibrator']:
            summary_text += (
                "There was a significative calibrator psd variation at "
                f"{warning}\n"
            )

    print(summary_text)

    summary_text = MIMEText(summary_text)
    summary_text['subject'] = (
        f"Monitoring results {datetime.today().strftime('%B %d, %Y')}"
    )

    mail.send_mail(summary_text)


def round_interval(interval):
    return interval - (interval % 5) if (interval - (interval % 5) > 0) else 5


def main(args):
    MEAN_DAYS_PERIOD = 14
    files = []
    psd_memory = {}
    stations = args.stations

    args.interval = round_interval(args.interval)
    # 1440 minutes per day (24 * 60)
    detection_condition_value = int((MEAN_DAYS_PERIOD * 1440) / args.interval)

    # get all the system ids from the requested locations
    if len(stations) == 0:
        systems = sys.get_station_ids()
    else:
        systems = sys.get_station_ids(stations, False)

    system_ids = [
        systems[lcode][antenna]
        for lcode in systems.keys()
        for antenna in systems[lcode].keys()
    ]

    if args.directory == default_dir:
        from_archive = True
    else:
        from_archive = False

    # get the start and end date
    start_date, end_date = get_dates(args.start_date, args.end_date)
    pre_start = start_date - timedelta(days=MEAN_DAYS_PERIOD)

    interval_delta = timedelta(minutes=args.interval)
    day_delta = timedelta(days=1)
    interval_sec = interval_delta.total_seconds()
    tqdm_day_value = day_delta.total_seconds() / interval_sec

    difference = (
        (end_date - start_date).total_seconds()
        / interval_sec
    )

    # get previous psd values
    pre_psd = f.get_previous_all_psd(
        system_ids,
        pre_start,
        end_date,
        args.interval,
    )

    for lcode in tqdm(
        systems.keys(),
        position=0,
        desc='Calculating for each station...'
    ):
        for antenna in systems[lcode].keys():
            sys_id = systems[lcode][antenna]
            requested_date = pre_start
            previous_noise = []
            previous_dates = []
            previous_calibrator = []
            sys_in_pre_psd = sys_id in pre_psd.keys()

            if sys_in_pre_psd:
                # first loop trough the previous psd values in order to get the
                # requested dates
                while requested_date < start_date:
                    str_date = requested_date.strftime('%Y-%m-%d %H:%M')
                    if str_date in pre_psd[sys_id].keys():
                        previous_noise.append(
                            pre_psd[sys_id][str_date]['noise']
                        )
                        previous_dates.append(str_date)
                        previous_calibrator.append(
                            pre_psd[sys_id][str_date]['calibrator']
                        )

                    requested_date += interval_delta

            requested_date = start_date
            pre_psd_length = len(previous_dates)

            with tqdm(
                total=difference,
                position=1,
                desc=f'{lcode}, antenna {antenna}',
            ) as pbar:
                # perform the monitoring on the whole time interval
                while requested_date < end_date:
                    calculate = True
                    str_date = requested_date.strftime('%Y-%m-%d %H:%M')
                    # if it is the first (during program execution) time that
                    # psd will be calculated for this station
                    if sys_id not in psd_memory.keys():
                        # add a dict to the noise_memory variable representing
                        # psd values for the current station
                        psd_memory[sys_id] = {
                            "title": f'{lcode}{antenna}',
                            "i": len(previous_noise) - 1,
                            "x": previous_dates,
                            "n_y": previous_noise,
                            "c_y": previous_calibrator,
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

                    if sys_in_pre_psd:
                        if (
                            str_date in pre_psd[sys_id].keys()
                            and not args.overwrite
                        ):
                            noise_psd = pre_psd[sys_id][str_date]['noise']
                            calibrator_psd = (
                                pre_psd[sys_id][str_date]['calibrator']
                            )
                            calculate = False

                    if calculate:
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

                        noise_psd = Decimal(psd.get_noise_psd(wav))
                        calibrator_psd, calibrator_f = (
                            psd.get_calibrator_psd(wav)
                        )
                        calibrator_psd = Decimal(calibrator_psd)

                        files.append({
                            "system_id": sys_id,
                            "time": str_date,
                            "noise_psd": noise_psd,
                            "calibrator_psd": calibrator_psd
                        })

                    # increment the counter, append an x value and append the
                    # psd value to the y array
                    sys_psd['i'] += 1
                    sys_psd['x'].append(str_date)
                    sys_psd['n_y'].append(noise_psd)
                    sys_psd['c_y'].append(calibrator_psd)

                    # if there is at least 12 days of psd data available
                    # check for marginal noise/calibrator variations
                    if sys_psd['i'] >= detection_condition_value:
                        print(sys_psd['i'], detection_condition_value)
                        relevant_noise_y = (
                            sys_psd
                            ['n_y']
                            [-detection_condition_value:]
                        )
                        noise_variations = variations.detect_noise_variations(
                            relevant_noise_y,
                            noise_psd,
                        )
                        # detect high noise increases
                        if noise_variations > 0:
                            sys_psd['warnings']['noise']['asc'].append(
                                wav.date.strftime('%Y-%m-%d %H:%M')
                            )

                        # do the same, but this time check for high noise
                        # decreases
                        elif noise_variations < 0:
                            sys_psd['warnings']['noise']['desc'].append(
                                wav.date.strftime('%Y-%m-%d %H:%M')
                            )

                        relevant_calibrator_y = (
                            sys_psd
                            ['c_y']
                            [-detection_condition_value:]
                        )
                        calibrator_variations = (
                            variations.detect_calibrator_variations(
                                relevant_calibrator_y,
                                calibrator_psd
                            )
                        )

                        # check for high calibrator psd increase
                        if calibrator_variations > 0:
                            sys_psd['warnings']['calibrator'].append(
                                (
                                    wav.date.strftime('%Y-%m-%d %H:%M'),
                                    calibrator_f
                                )
                            )

                        # check for high calibrator psd decrease
                        elif calibrator_variations < 0:
                            sys_psd['warnings']['calibrator'].append(
                                (
                                    wav.date.strftime('%Y-%m-%d %H:%M'),
                                    calibrator_f
                                )
                            )

                    requested_date += interval_delta
                    pbar.update(1)

    f.insert_psd(files)
    send_summary(psd_memory)

    if args.json:
        with open('test_data.json', 'w') as json_file:
            json.dump(psd_memory, json_file)

        with open('file_data.json', 'w') as json_file:
            json.dump(files, json_file)

    if args.plot or args.ymin is not None or args.ymax is not None:
        for i, sys_id in enumerate(psd_memory.keys()):
            generate_plot(
                psd_memory[sys_id]['x'][pre_psd_length:],
                psd_memory[sys_id]['n_y'][pre_psd_length:],
                f"{psd_memory[sys_id]['title']}_"
                f"{args.start_date}_{args.end_date}_noise",
                figure_n=i,
                title=f"{psd_memory[sys_id]['title']} noise",
                y_title='ADU',
                x_title='date',
                y_min=args.ymin,
                y_max=args.ymax,
            )
            generate_plot(
                psd_memory[sys_id]['x'][pre_psd_length:],
                psd_memory[sys_id]['c_y'][pre_psd_length:],
                f"{psd_memory[sys_id]['title']}_"
                f'{args.start_date}_{args.end_date}_calibrator',
                figure_n=i + len(psd_memory.keys()),
                title=f"{psd_memory[sys_id]['title']} calibrator",
                y_title='ADU',
                x_title='date',
                y_min=args.ymin,
                y_max=args.ymax,
            )


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
    y_min=None,
    y_max=None,
):
    if not len(x) or not len(y) or not len(x) == len(y):
        return

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
        description="""
            This program has two purposes. The first is to calculate and store
            the mean psd of the noise and calibrator levels in the BRAMS wav
            file. Its second purpose is to detect of there are high variations
            of those psd values from one file to another, coming from the same
            station of course.\n
            There are 2 ways to launch this program. The first is automatic
            mode, in this case you don't specify any argument and the program
            will figure out what it has to do. The second way is in manual
            mode in which case you simply have to specify the START DATE and
            END DATE arguments.
        """
    )
    parser.add_argument(
        'start_date',
        metavar='START DATE',
        help="""
            Date to start calculating the mean noise and calibrator psd values,
            and detecting high psd variations. The format of this date must be
            YYYY-MM-DD. Note that this date cannot be in the future.\n
            If this argument is not given, the program will search for the
            date written in the program_data.json file. If, however, there is
            no program_data.json file, it will default to the actual time
            minus 24 hours.
        """,
        nargs='?',
        default=None
    )
    parser.add_argument(
        'end_date',
        metavar='END DATE',
        help="""
            calculating the mean noise and calibrator psd values,
            and detecting high psd variations. The format of this date must be
            YYYY-MM-DD. Note that this date cannot be in the future.\n
            If this argument is not given, the program will set this argument
            to the actual date and time.
        """,
        nargs='?',
        default=None
    )
    parser.add_argument(
        'stations',
        metavar='STATIONS',
        help="""
            List of station codes (BEGRIM, ...) for which to calculate psd
            values and detect high noise/calibrator psd values. If there is no
            station given, the program will calculate psd values for every
            existing station.
        """,
        nargs='*',
        default=[]
    )
    parser.add_argument(
        '-i', '--interval',
        help="""
            This argument specifies the interval between each file to
            calculate. This value must be a value in minutes. Its default
            value is 60 (1 hour).
        """,
        default=60,
        type=int,
        nargs='?'
    )
    parser.add_argument(
        '-d', '--directory',
        help=f"""
            Path to the directory containing the files to calculate the psd
            values of. This value defaults to {default_dir}.
        """,
        default=default_dir,
        type=str,
        nargs='?'
    )
    parser.add_argument(
        '-o', '--overwrite',
        help="""
            If this flag is set, any psd values that are already present in
            the database will be overwritten. Note that this may take more
            time, since the psd has to be calculated for each file.
        """,
        action='store_true'
    )
    parser.add_argument(
        '-p', '--plot',
        help="""
            If this flag is set, the program will generate plots of the
            calculated data. The plots are stored as png files and their name
            is written as followed :
            [location_code][antenna]_[start]_[end]_[calibrator/noise].
            By default, the plots won't be limited in frequency. If however
            you'd like them to be limited in frequency, specify the -f
            (--fmin) and the -F (--fmax) arguments.
        """,
        action='store_true'
    )
    parser.add_argument(
        '-f', '--fmin',
        help="""
            Specifies the minimum frequency value the plot will show on its
            y axis.
        """,
        default=None,
        type=int,
        nargs='?'
    )
    parser.add_argument(
        '-F', '--fmax',
        help="""
            Specifies the maximum frequency value the plot will show on its
            y axis.
        """,
        default=None,
        type=int,
        nargs='?'
    )
    parser.add_argument(
        '-j', '--json',
        help="""
            If this flag is set, a file named file_data.json will be generated
            by the program. This file contains the calibrator and noise psd
            for each file asked by the user.
        """,
        action='store_true',
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

import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
import geopy.distance as geo
import modules.database.system as sys
import modules.database.file as fil
import modules.meteor_detect.csv as csv

# from modules.brams_wav_2 import BramsWavFile
from modules.brams_wav import BramsError, BramsWavFile
from modules.meteor_detect.spectrogram import Spectrogram
from datetime import datetime, timedelta, timezone
from scipy.fft import rfft, rfftfreq
from scipy.signal import windows
from typing import Union

# default_dir = 'recordings/'
default_dir = '/bira-iasb/data/GROUNDBASED/BRAMS/wav/'
# 2022-04-23T000212 BEHUMA


def get_interval(string_date='2022-04-29T000000'):
    if '-' in string_date:
        date_format = '%Y-%m-%d'
    elif '/' in string_date:
        date_format = '%Y/%m/%d'
    else:
        date_format = '%Y%m%d'

    if ':' in string_date:
        time_format = '%H:%M:%S'
    else:
        time_format = '%H%M%S'

    if 'T' in string_date:
        utc0_date = datetime.strptime(
            string_date, f'{date_format}T{time_format}')
    elif 't' in string_date:
        utc0_date = datetime.strptime(
            string_date, f'{date_format}t{time_format}')
    elif '_' in string_date:
        utc0_date = datetime.strptime(
            string_date, f'{date_format}_{time_format}')
    else:
        utc0_date = datetime.strptime(
            string_date, f'{date_format}{time_format}')

    utc0_date = utc0_date.replace(tzinfo=timezone.utc)

    return {
        'start_time': (
            datetime.timestamp(utc0_date - timedelta(seconds=3))
            * 1000000
        ),
        'occurence_time': datetime.timestamp(utc0_date) * 1000000,
        'end_time': (
            datetime.timestamp(utc0_date + timedelta(seconds=3))
            * 1000000
        )
    }


def get_meteor_specs(wav_file, meteor_coords=[]):
    for meteor in meteor_coords:
        start = math.floor(meteor['t_start'] / 1000000 * wav_file.fs)
        stop = math.ceil(meteor['t_stop'] / 1000000 * wav_file.fs)

        print(f"{meteor['t_start'] / 1000000}-->{start}")
        print(f"{meteor['t_stop'] / 1000000}-->{stop}")
        meteor_samples = wav_file.Isamples[
            start:
            stop
        ]

        w = windows.hann(meteor_samples.size)
        w_scale = 1 / w.mean()

        Isamples = meteor_samples * w * w_scale
        yf = rfft(Isamples)
        xf = rfftfreq(meteor_samples.size, (1 / wav_file.fs))

        plt.figure(10)
        plt.plot(xf, np.abs(yf))


def get_meteor_coords(
    stations: dict,
    interval: dict,
    is_wav: bool,
    directory: str,
    from_archive: bool
):
    # filter matrix
    # its primary purpose is to amplify long vertical elements
    kernel = np.zeros((27, 7))
    kernel[12:15, 0] = -1.5
    kernel[12:15, -1] = -1.5

    kernel[0:2, 3] = 50
    kernel[-1, 3] = 50
    kernel[-2, 3] = 50

    # for each relevant wav file
    for location in stations.keys():
        for antenna in stations[location]['sys'].keys():
            for date in stations[location]['sys'][antenna].keys():
                system_file = stations[location]['sys'][antenna][date]
                system_file['meteors'] = []

                # print(f"\nSearching in file {system_file['file_path']}.")

                try:
                    # read the wav file
                    wav = BramsWavFile(
                        datetime.strptime(date, '%Y%m%d%H%M'),
                        location,
                        f"SYS{antenna.rjust(3, '0')}",
                        respect_date=True,
                        parent_directory=directory,
                        is_wav=is_wav,
                        from_archive=from_archive,
                    )
                except BramsError:
                    continue

                # generate the spectrogram
                spectrogram = Spectrogram(
                    wav.Isamples,
                    sample_frequency=wav.fs
                )

                # calculate the time resolution of the spectrogram
                # by comparing the time length of the spectrogram and the time
                # length in microseconds
                spectrogram_length = len(spectrogram.times)
                time_length = system_file['end'] - system_file['start']
                spectrogram_res = spectrogram_length / time_length
                # time_res = time_length / spectrogram_length

                # get the start index of the interval on the spectrogram
                interval_start = math.floor(
                    (interval['start_time'] - system_file['start'])
                    * spectrogram_res
                )
                broad_interval_start = interval_start - 23

                # get the end index of the interval on the spectrogram
                interval_end = math.ceil(
                    (interval['end_time'] - system_file['start'])
                    * spectrogram_res
                )
                broad_interval_end = interval_end + 23

                # filter the spectrogram in order to find meteors
                spectrogram.filter_with_kernel(
                    start=broad_interval_start,
                    end=broad_interval_end,
                    kernel=kernel
                )
                spectrogram.filter_by_percentile(
                    start=broad_interval_start,
                    end=broad_interval_end,
                    percentile=95
                )
                spectrogram.delete_area(
                    6 / spectrogram.frequency_resolution,
                    start=broad_interval_start,
                    end=broad_interval_end,
                )
                spectrogram.filter_with_kernel(
                    start=broad_interval_start,
                    end=broad_interval_end,
                )
                # find the unprecise meteor coords
                coords = spectrogram.get_potential_meteors(
                    start=interval_start,
                    end=interval_end,
                    broad_start=broad_interval_start,
                    broad_end=broad_interval_end,
                )
                # spectrogram.plot_modified_spectrogram(
                #     interval=250,
                #     show=True,
                #     title=system_file['file_path']
                # )

                # find a more precise representation of the meteor coords
                specs = spectrogram.get_meteor_specs(coords)
                print(
                    f"Found {len(specs)} meteors is file "
                    f"{system_file['file_path']}."
                )

                system_file['meteors'] = specs

    return stations


def get_close(stations, reference_station_code=None):
    if reference_station_code is None:
        for location in stations:
            location['distance'] = None
    else:
        ref_station = stations[reference_station_code]
        for location in stations.keys():
            stations[location]['distance'] = geo.distance(
                (ref_station['latitude'], ref_station['longitude']),
                (
                    stations[location]['latitude'],
                    stations[location]['longitude']
                )
            )

    return stations


def generate_filename(
    basis: str = 'meteor_detect',
    date: Union[datetime, None] = None,
    station: Union[str, None] = None
):
    if date is None:
        date = ''
    else:
        date = '_' + date.strftime('%Y%m%d_%H%M%S')

    if station is None:
        station = ''
    else:
        station = '_' + station

    return f'{basis}{date}{station}'


def main(args):
    # get the interval in which to detect meteors
    interval = get_interval(args.detection_time[0])
    systems = []
    system_ids = []
    if len(args.stations) == 0:
        systems = sys.get_station_ids()
    else:
        systems = sys.get_station_ids(args.station, False)

    # restructure the system ids in a simple list instead of dictionnary
    for lcode in systems.keys():
        for antenna in systems[lcode].keys():
            system_ids.append(systems[lcode][antenna])

    stations = fil.get_file_by_interval(system_ids, interval)

    if stations == {}:
        print('No files were found for those stations at that time.')
        return

    if args.file_directory == default_dir:
        from_archive = True
    else:
        from_archive = False

    # get distance between stations and reference stations
    stations = get_close(stations, args.reference_station)
    stations = get_meteor_coords(
        stations,
        interval,
        args.wav,
        args.file_directory,
        from_archive
    )

    csv.write_csv(
        stations,
        filename=generate_filename(
            date=datetime.fromtimestamp(
                interval['occurence_time'] / 1000000,
                tz=timezone.utc
            ),
            station=args.reference_station
        ),
        directory=args.csv_destination
    )


def main_test():
    directory = './recordings/meteor_search/'
    kernel = np.zeros((27, 7))
    kernel[12:15, 0] = -1.5
    kernel[12:15, -1] = -1.5

    kernel[0:2, 3] = 50
    kernel[-1, 3] = 50
    kernel[-2, 3] = 50

    print(kernel)

    print("Loading wav file into memory...")
    wav_file = BramsWavFile(
        datetime.strptime('202202111800', '%Y%m%d%H%M')
        .replace(tzinfo=timezone.utc),
        'BEHUMA',
        "SYS001",
        respect_date=True,
        parent_directory=directory,
        is_wav=True,
        from_archive=False,
    )

    test_spectrogram = Spectrogram(
        wav_file.Isamples,
        sample_frequency=wav_file.fs
    )
    test_spectrogram.filter_with_kernel(
        filter_all=True, coefficient=1, kernel=kernel
    )
    test_spectrogram.filter_by_percentile(filter_all=True, percentile=95)

    test_spectrogram.delete_area(15, delete_all=True)
    test_spectrogram.filter_with_kernel(filter_all=True, coefficient=1)
    test_spectrogram.get_potential_meteors(get_all=True)
    # test_spectrogram.get_meteor_specs(coords)

    test_spectrogram.plot_original_spectrogram(250)
    test_spectrogram.plot_modified_spectrogram(250, show=True)


def arguments():
    parser = argparse.ArgumentParser(
        description="""
            Program searches for meteor detection found on one system
            on other systems and returns the result in a csv file.
            To use this program, enter the program name followed by the
            date and time you want to search the stations for meteors.
            Additional options are listed below.
        """
    )
    parser.add_argument(
        'detection_time',
        metavar='DETECTION TIME',
        help="""
            Time ot the meteor detection use either 'YYYYMMDDThhmmss' or
            'YYYYMMDD_hhmmss' format to specify the date and the time.
            All other formats are prone to fail.
        """,
        nargs=1
    )
    parser.add_argument(
        'reference_station',
        metavar='REFERENCE STATION',
        help="""
            Station where the meteor signal was detected and from where
            the distance between other stations will be calculated. This
            means that, if a meteor detection was found on another
            station, the location between the reference station and that
            station will be given.
            If this argument in not specified, the program will simply
            look for meteors on all of the available wav files at the
            specified detection time.
        """,
        nargs='?',
        default=None
    )
    parser.add_argument(
        '-s', '--stations',
        help="""
            Stations where to look for the detected meteor signal.
            If no stations is specified, the program will look for the
            meteor signal on all available wav files at the meteor the
            specified detection time.
        """,
        nargs='*',
        default=[]
    )
    parser.add_argument(
        '-d', '--file-directory',
        help=f"""
            Directory where to get the wav files. If no directory is
            specified, the program will look for files in the
            {default_dir} directory and according to the specified date.
        """,
        nargs='?',
        type=str,
        default=default_dir
    )
    parser.add_argument(
        '-c', '--csv-destination',
        help="""
            Destination file/directory of the results csv file. If the
            destination is a folder, the file's name will be
            'meteor_detect_YYYYMMDD_hhmmss[_LOCATION].csv'.
            This argument can be ignored in which case the destination
            file will be stored in the current directory.
        """,
        nargs='?',
        default=None
    )
    parser.add_argument(
        '-w', '--wav',
        help="""
            Indicates if the file in the specified directory are .wav files.
            If this flag is not set, the program will search for .tar files.
        """,
        action='store_true'
    )

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main_test()
    # args = arguments()
    # main(args)
    # print('Exiting...')

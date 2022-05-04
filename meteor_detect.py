import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
import geopy.distance as geo
import modules.database.system as sys
import modules.database.file as fil
import modules.meteor_detect.archive as arch
import modules.meteor_detect.csv as csv

from modules.brams_wav_2 import BramsWavFile
from modules.meteor_detect.spectrogram import Spectrogram
from datetime import datetime, timedelta, timezone
from scipy.fft import rfft, rfftfreq
from scipy.signal import windows

default_dir = 'recordings/'
# default_dir = /bira-iasb/data/GROUNDBASED/BRAMS/
# 2022-04-23T000212 BEHUMA


def get_interval(string_date='2022-04-29T000000'):
    if 'T' in string_date:
        utc0_date = datetime.strptime(string_date, '%Y-%m-%dT%H%M%S')
    elif 't' in string_date:
        utc0_date = datetime.strptime(string_date, '%Y-%m-%dt%H%M%S')
    elif '_' in string_date:
        utc0_date = datetime.strptime(string_date, '%Y-%m-%d_%H%M%S')
    else:
        return False

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


def get_meteor_coords(stations, interval):
    # filter matrix
    # its primary purpose is to amplify long vertical elements
    kernel = [
        [0.,   0.,   0.,  50.,   0.,   0.,   0.],
        [0.,   0.,   0.,  50.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [-1.5, 0.,   0.,   0.,   0.,   0.,  -1.5],
        [-1.5, 0.,   0.,   0.,   0.,   0.,  -1.5],
        [-1.5, 0.,   0.,   0.,   0.,   0.,  -1.5],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,   0.,   0.,   0.,   0.],
        [0.,   0.,   0.,  50.,   0.,   0.,   0.],
        [0.,   0.,   0.,  50.,   0.,   0.,   0.]
    ]

    # for each relevant wav file
    for location in stations.keys():
        for antenna in stations[location]['sys'].keys():
            for date in stations[location]['sys'][antenna].keys():
                system_file = stations[location]['sys'][antenna][date]
                system_file['meteors'] = []

                if system_file['file_path'] is None:
                    continue

                # read the wav file
                wav = BramsWavFile(
                    system_file['file_path']
                )

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
                print(interval_start, interval_end)

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
                    15,
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
                    end=interval_end
                )
                print(coords)
                # find a more precise representation of the meteor coords
                specs = spectrogram.get_meteor_specs(coords)

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

    stations = arch.get_archived_files(
        stations,
        datetime.fromtimestamp(interval['occurence_time'] / 1000000),
        default_dir
    )

    # get distance between stations and reference stations
    stations = get_close(stations, args.reference_station)
    stations = get_meteor_coords(stations, interval)

    csv.write_csv(stations)


def main_test(cmd_arguments):
    print(cmd_arguments)
    kernel = np.zeros((27, 7))
    kernel[12:15, 0] = -1.5
    kernel[12:15, -1] = -1.5

    kernel[0:2, 3] = 50
    kernel[-1, 3] = 50
    kernel[-2, 3] = 50

    print(kernel)

    print("Loading wav file into memory...")
    wav_file = BramsWavFile(
        './recordings/2022/04/23/RAD_BEDOUR_20220423_0000_BEHUMA_SYS001.wav'
    )

    test_spectrogram = Spectrogram(
        wav_file.Isamples,
        sample_frequency=wav_file.fs
    )
    test_spectrogram.filter_with_kernel(
        filter_all=True, coefficient=1, kernel=kernel
    )
    test_spectrogram.filter_by_percentile(filter_all=True, percentile=95)
    # test_spectrogram.filter_with_kernel(filter_all=True, coefficient=1)

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
            station id or the station location_code with the staion
            antenna number attached to it (i.e. BEHAAC1, BEHUMA3, ...).
            If this argument in not specified, the program will simply
            look for meteors on all of the available wav files at the
            specified detection time.
        """
    )
    parser.add_argument(
        'detection_time',
        metavar='DETECTION TIME',
        help="""
            Time ot the meteor detection use either '%Y-%m-%dT%H%i' or
            '%Y-%m-%d_%H%i' format to specify the date and the time.
            All other formats are prone to fail.
        """,
        nargs=1
    )
    parser.add_argument(
        'reference_station',
        metavar='REFERENCE STATION',
        help="""
            Stations where the meteor signal was detected and from where
            the distance between other stations will be calculated. This
            means that, if a meteor detection was found on another
            station that was not specified in this list, that station's
            location will be compared to all the station's location
            of this list.
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
        default=None
    )
    parser.add_argument(
        '-c', '--csv-destination',
        help="""
            Destination file/directory of the results csv file. If the
            destination is a folder, the file's name will be
            'meteor_detect_YYYYMMDD_HHmmss.csv'.
            This argument can be ignored in which case the destination
            file will be stored in the current directory.
        """,
        nargs='?',
        default=None
    )

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = arguments()
    main(args)
    print('Exiting...')

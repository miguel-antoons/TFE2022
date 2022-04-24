import argparse
import os
import modules.psd.database as db
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from tqdm import tqdm
from scipy import signal
from modules.brams_wav_2 import BramsWavFile
from modules.psd.psd import SSB_noise


default_dir = 'recordings/'


def main(args):
    start_date = datetime.strptime(args.start_date[0], '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    stations = args.stations
    station_ids = db.get_station_ids(stations)

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
            file_path = os.path.join(directory, filename)
            # check the path is a file
            if os.path.isfile(file_path):
                asked_files.append({
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

    print('Calculating psd for each file...')

    # calculating psd for each file
    for file in tqdm(asked_files):
        f = BramsWavFile(file['filename'])
        frequencies, times, Pxx = signal.spectrogram(
            f.Isamples,
            f.fs,
            nperseg=16384,
            noverlap=14384,
            window='hann',
        )
        frequency_resolution = f.fs / 2 / len(frequencies)
        calibrator_frequency = find_calibrator(
            Pxx,
            frequency_resolution,
            search_length=len(times)
        )

        if calibrator_frequency:
            psd = SSB_noise(f, calibrator_frequency - 5, calibrator_frequency + 5)
            print(psd)
            file["psd"] = psd
            file['calibrator_frequency'] = calibrator_frequency
        else:
            file["psd"] = None
            file['calibrator_frequency'] = None

def find_calibrator(Pxx, frequency_resolution, search_length=50, fmin=1350, fmax=1650):
    same_index = 0
    previous_index = 0
    index = 0
    min_row = round(fmin / frequency_resolution)
    max_row = round(fmax / frequency_resolution)

    print(f'Searching direct signal between {fmin} Hz and {fmax} Hz...')

    while not same_index == 50 and index < search_length:
        max_column_index = Pxx[min_row:max_row, index].argmax()

        if max_column_index in [
            previous_index - 1, previous_index, previous_index + 1
        ]:
            same_index += 1
        else:
            same_index = 0
            previous_index = max_column_index

        index += 1

    if same_index < 50:
        print(
            'Calibrator signal was not found, therefore psd cannot be '
            'calculated.'
        )
        return False

    print(
        'Direct signal was found around '
        f'{(previous_index + min_row) * frequency_resolution} Hz.'
    )
    return (previous_index + min_row) * frequency_resolution


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


def get_audio_signal():
    ...


if __name__ == '__main__':
    args = argparse.Namespace(
        start_date=['2021-07-01'],
        end_date='2021-08-31',
        stations=['BEHAAC'],
        directory=default_dir,
    )
    # args = argparse.Namespace(
    #     start_date=['2020-06-01'],
    #     end_date='2020-09-30',
    #     stations=['BEOOSE'],
    #     directory=default_dir,
    # )
    # args = arguments()
    main(args)

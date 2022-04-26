import sys
import argparse
import numpy as np

from modules.brams_wav_2 import BramsWavFile
from modules.meteor_detect.spectrogram import Spectrogram


def main(cmd_arguments):
    print(cmd_arguments)
    kernel = np.zeros((27, 7))
    kernel[12:15, 0] = -1.5
    kernel[12:15, -1] = -1.5

    kernel[0:2, 3] = 50
    kernel[-1, 3] = 50
    kernel[-2, 3] = 50
    # kernel = np.zeros((53, 7))
    # kernel[25:28, 0] = -1.5
    # kernel[25:28, -1] = -1.5

    # kernel[0:2, 3] = 30
    # kernel[26:28, 3] = 5
    # kernel[2:25, 3] = 1/23

    print(kernel)

    print("Loading wav file into memory...")
    wav_file = BramsWavFile(
        './recordings/meteor_search/RAD_BEDOUR_20220211_1735_BEHUMA_SYS001.wav'
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

    # test_spectrogram.filter_by_percentile(filter_all=True, percentile=96)
    # test_spectrogram.filter_with_kernel(filter_all=True)
    # test_spectrogram.get_potential_meteors(get_all=True)

    test_spectrogram.plot_original_spectrogram(250)
    test_spectrogram.plot_modified_spectrogram(250, show=True)
    # test_spectrogram.plot_original_spectre(temp_start, temp_end, fmin, fmax)
    # test_spectrogram.plot_modified_spectre(
    #     temp_start, temp_end, fmin, fmax, True
    # )


def arguments():
    parser = argparse.ArgumentParser(
        description="""
            Program searches for meteor detection found on one system
            on other systems.
            To use this program, enter the program name followed by the
            station id or the station location_code with the staion
            antenna number attached to it (i.e. BEHAAC1, BEHUMA3, ...).
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


if __name__ == '__main__':
    args = arguments()
    main(args)
    print('Exiting...')

import sys
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
    wav_file = BramsWavFile(
        './recordings/BEHAAC/RAD_BEDOUR_20200602_0000_BEHAAC_SYS001.wav'
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


if __name__ == '__main__':
    main(sys.argv)
    print('Exiting...')

import sys
from scipy.io import wavfile
from program_files.spectrogram import Spectrogram
import numpy as np


def main(cmd_arguments):
    print(cmd_arguments)
    kernel = np.zeros((27, 7))
    kernel[12:15, 0] = -1
    kernel[12:15, -1] = -1
    kernel[3:-3, 3] = 1
    kernel[2, 3] = 7
    kernel[-3, 3] = 7
    kernel[1, 3] = 8
    kernel[-2, 3] = 8
    kernel[0, 3] = 9
    kernel[-1, 3] = 9
    # kernel[21:, 3] = 5
    # kernel[0, 0] = -1
    # kernel[-1, -1] = -1
    # temp_start = 354
    # temp_end = 355
    print(kernel)

    print("Loading wav file into memory...")
    sample_frequency, audio_signal = wavfile.read(
        './recordings/RAD_BEDOUR_20220211_1735_BEDINA_SYS001.wav'
    )

    test_spectrogram = Spectrogram(audio_signal)
    # test_spectrogram.filter_high(0.1, filter_all=True)
    # test_spectrogram.filter_low(filter_all=True)
    test_spectrogram.filter_with_kernel(
        filter_all=True, coefficient=1, kernel=kernel
    )
    test_spectrogram.filter_low(filter_all=True)
    # test_spectrogram.filter_with_kernel(
    #     filter_all=True
    # )
    # test_spectrogram.filter_by_mean(filter_all=True)

    test_spectrogram.delete_area(27, delete_all=True)

    # # test_spectrogram.filter_with_kernel(filter_all=True, coefficient=1)
    # test_spectrogram.count_meteors(2, 0, 818)

    test_spectrogram.plot_original_spectrogram(250)
    test_spectrogram.plot_modified_spectrogram(250, show=True)
    # test_spectrogram.plot_original_spectre(temp_start, temp_end, fmin, fmax)
    # test_spectrogram.plot_modified_spectre(
    #     temp_start, temp_end, fmin, fmax, True
    # )


if __name__ == '__main__':
    main(sys.argv)
    print('Exiting...')

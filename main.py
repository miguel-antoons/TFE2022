import sys
from scipy.io import wavfile
from program_files.spectrogram import Spectrogram


def main(cmd_arguments):
    print(cmd_arguments)
    # temp_start = 354
    # temp_end = 355

    print("Loading wav file into memory...")
    sample_frequency, audio_signal = wavfile.read(
        './recordings/RAD_BEDOUR_20220211_1730_BEDINA_SYS001.wav'
    )

    test_spectrogram = Spectrogram(audio_signal)
    test_spectrogram.filter_high(0.1, filter_all=True)
    test_spectrogram.filter_with_kernel(filter_all=True, coefficient=2)

    # test_spectrogram.filter_low(filter_all=True)
    # test_spectrogram.filter_with_kernel(filter_all=True, coefficient=2)
    for i in range(819):
        test_spectrogram.delete_area(25, i)

    # test_spectrogram.filter_with_kernel(filter_all=True, coefficient=1)
    test_spectrogram.count_meteors(2, 0, 818)

    test_spectrogram.plot_original_spectrogram(150)
    test_spectrogram.plot_modified_spectrogram(150, show=True)
    # test_spectrogram.plot_original_spectre(temp_start, temp_end, fmin, fmax)
    # test_spectrogram.plot_modified_spectre(
    #     temp_start, temp_end, fmin, fmax, True
    # )


if __name__ == '__main__':
    main(sys.argv)
    print('Exiting...')

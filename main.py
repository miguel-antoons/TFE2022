from scipy.io import wavfile
from program_files.spectrogram import Spectrogram


def main():
    temp_start = 350
    temp_end = 360
    fmin = 1000
    fmax = 1150

    print("Loading wav file into memory...")
    sample_frequency, audio_signal = wavfile.read(
        './recordings/RAD_BEDOUR_20220211_1730_BEDINA_SYS001.wav'
    )

    test_spectrogram = Spectrogram(audio_signal)

    # test_spectrogram.filter_by_mean(temp_start, temp_end, 2)
    # test_spectrogram.filter_with_kernel(temp_start, temp_end, coefficient=2)
    # test_spectrogram.plot_original_spectrogram(fmin=fmin, fmax=fmax)
    # test_spectrogram.plot_modified_spectrogram(fmin=fmin, fmax=fmax)
    # test_spectrogram.plot_original_spectre(temp_start, temp_end, fmin, fmax)
    # test_spectrogram.plot_modified_spectre(
    #     temp_start, temp_end, fmin, fmax, True
    # )
    print(test_spectrogram.get_mean_value(2, 2))


if __name__ == '__main__':
    main()
    print('Exiting...')

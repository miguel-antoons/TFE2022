import numpy as np
import matplotlib.pyplot as plt

from scipy import signal
from modules.brams_wav_2 import BramsWavFile


def main():
    f = BramsWavFile(
        './recordings/BEHAAC/RAD_BEDOUR_20200602_0000_BEHAAC_SYS001.wav'
    )
    frequencies, times, Pxx = signal.spectrogram(
        f.Isamples,
        f.fs,
        nperseg=16384,
        noverlap=14384,
        window='hann',
    )
    frequency_resolution = f.fs / 2 / len(frequencies)
    indexes = find_calibrator(Pxx, frequency_resolution, search_length=len(times))


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
            'Direct signal was not found, spectrogram will be '
            'shown around default value of 1000 Hz.'
        )
        return False, False, round(1500 / frequency_resolution)

    print(
        'Direct signal was found around '
        f'{(previous_index + min_row) * frequency_resolution} Hz.'
    )
    return (
        (previous_index + min_row - 2),
        (previous_index + min_row + 3),
        (previous_index + min_row)
    )


def get_audio_signal():
    ...


if __name__ == '__main__':
    main()

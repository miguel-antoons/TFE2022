from scipy import signal
from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt


def main():
    print("Loading wav file into memory...")
    sample_frequency, audio_signal = wavfile.read(
        './recordings/RAD_BEDOUR_20220211_1730_BEDINA_SYS001.wav'
    )
    print(f'Sample frequency : {sample_frequency}')
    print(f'Signal length : {len(audio_signal)}')

    print('Calculating spectrogram...')
    frequencies, times, spectrogram = signal.spectrogram(
        audio_signal, sample_frequency, nperseg=16384
    )

    print('Filtering unneeded frequencies...')
    fmin = 1000
    fmax = 1200
    freq_slice = np.where((frequencies >= fmin) & (frequencies <= fmax))
    frequencies = frequencies[freq_slice]
    spectrogram = spectrogram[freq_slice, :][0]

    print(f'Sample frequencies : {frequencies}')
    print(f'Segment times : {times}')

    print('Preparing and showing graph...')
    plt.pcolormesh(times, frequencies, spectrogram, shading='auto', norm=1.0)
    # plt.imshow(spectrogram)
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.show()


if __name__ == '__main__':
    main()

from scipy.io import wavfile
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt


def main():
    nfft = 16384
    overlap_samples = 14384

    print("Loading wav file into memory...")
    sample_frequency, audio_signal = wavfile.read(
        './recordings/RAD_BEDOUR_20220211_1730_BEDINA_SYS001.wav'
    )
    print(f'Sample frequency : {sample_frequency}')
    print(f'Signal length : {len(audio_signal)}')

    freqs, bins, Pxx = signal.spectrogram(
        audio_signal,
        sample_frequency,
        nperseg=nfft,
        noverlap=overlap_samples,
        window='hamming'
    )

    Pxx = np.array(Pxx, dtype=float)
    print('Filtering unneeded frequencies...')
    fmin = 1000
    fmax = 1150

    Pxx = Pxx[(freqs >= fmin) & (freqs <= fmax)]
    freqs = freqs[(freqs >= fmin) & (freqs <= fmax)]

    Z = 10. * np.log10(Pxx)
    Z = np.array(Z, dtype=float)
    plt.figure(1)
    #Z[:, 355] = 60
    Z2 = Z[:, 350:360]
    Z2_mean = np.mean(Z2)
    Z2[Z2 < (Z2_mean + Z2_mean / 3.5)] = 0
    plt.plot(freqs, Z2)

    print(f'Sample frequencies : {freqs}')
    print(f'Segment times : {len(bins)}')
    # print(f'Spectrogram values : {Pxx[62]}')
    print(f'Length of a spectre : {len(Pxx[62])}')
    print(f'Spectrogram 0, 62 : {Pxx[0][62]}')
    print(f'Spectrogram 0, 60 : {Pxx[0][60]}')

    print('Preparing and showing graph...')
    plt.figure(2)
    plt.pcolormesh(bins, freqs, Z)
    # plt.imshow(spectrogram)
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    # plt.colorbar()
    plt.show()


if __name__ == '__main__':
    main()

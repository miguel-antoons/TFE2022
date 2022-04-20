from scipy import signal, ndimage
import numpy as np
import matplotlib.pyplot as plt


def main():
    frequencies, times, Pxx = signal.spectrogram(
        audio_signal,
        5512,
        nperseg=16384,
        noverlap=14384,
        window='hamming',
    )


def get_audio_signal():
    


if __name__ == '__main__':
    main()

from scipy import signal
import numpy as np
import matplotlib.pyplot as plt

class Spectrogram:
    def __init__(self, audio_signal, nfft=16384, sample_frequency=5512, noverlap=14384, window='hamming'):
        frequencies, times, Pxx = signal.spectrogram(
            audio_signal,
            sample_frequency,
            nperseg=nfft,
            noverlap=noverlap,
            window=window
        )
        self.sample_frequency = sample_frequency
        self.frequencies = np.frombuffer(frequencies, dtype=float)
        self.times = np.frombuffer(times, dtype=float)
        self.Pxx = np.array(Pxx, dtype=float)
        self.Pxx_DB = 10. * np.log10(Pxx)

    def plot_spectrogram(
        self,
        figure_n=1,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        fmin=0,
        fmax=None,
        show=True
    ):
        print('Preparing spectrogram figure...')
        plt.figure(figure_n)
        plt.pcolormesh(self.times, self.frequencies, self.Pxx_DB)
        plt.ylabel(y_axis_title)
        plt.xlabel(x_axis_title)

        if show:
            plt.show()

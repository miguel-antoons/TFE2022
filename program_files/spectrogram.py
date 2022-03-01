from scipy import signal
import numpy as np
import matplotlib.pyplot as plt


class Spectrogram:
    def __init__(
        self,
        audio_signal,
        nfft=16384,
        sample_frequency=5512,
        noverlap=14384,
        window='hamming'
    ):
        frequencies, times, Pxx = signal.spectrogram(
            audio_signal,
            sample_frequency,
            nperseg=nfft,
            noverlap=noverlap,
            window=window,
        )
        print(f'Sample frequency : {sample_frequency}')
        print(f'Signal length : {len(audio_signal)}')
        # sample frequency of the wav audio signal
        self.sample_frequency = sample_frequency
        # frequencies contained by the audio signal
        self.frequencies = np.frombuffer(frequencies, dtype=float)
        # time segments contained in the audio signal
        self.times = np.frombuffer(times, dtype=float)
        # signal strength
        self.Pxx = np.array(Pxx, dtype=float)
        # signal strength in dB
        self.Pxx_DB = 10. * np.log10(Pxx)
        # copy of the signal strencgth in dB to be modified
        self.Pxx_DB_modified = self.Pxx_DB.copy()
        # initialize the figure number to 1
        self.figure_n = 1

    """
        Plot the original spectrogram
    """
    def plot_original_spectrogram(
        self,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        fmin=0,
        fmax=None,
        show=False
    ):
        # if fmax is not set, set default value
        if not fmax:
            fmax = self.sample_frequency / 2

        print('Preparing original spectrogram figure...')
        plt.figure(self.figure_n)    # create figure
        self.figure_n += 1
        # create a colormesh where x=times, y=frequencies and color=Pxx_DB
        plt.pcolormesh(
            self.times,
            self.frequencies[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ],
            self.Pxx_DB[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ]
        )

        # set axis titles
        plt.ylabel(y_axis_title)
        plt.xlabel(x_axis_title)

        if show:
            self.show_figures()

    """
        Plot the modified spectrogram
    """
    def plot_modified_spectrogram(
        self,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        fmin=0,
        fmax=None,
        show=False
    ):
        # if fmax is not set, set default value
        if not fmax:
            fmax = self.sample_frequency / 2

        print('Preparing modified spectrogram figure...')
        plt.figure(self.figure_n)    # create figure
        self.figure_n += 1
        # create a colormesh where x=times, y=frequencies and
        # color=Pxx_DB_modified
        plt.pcolormesh(
            self.times,
            self.frequencies[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ],
            self.Pxx_DB_modified[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ]
        )

        # set axis titles
        plt.ylabel(y_axis_title)
        plt.xlabel(x_axis_title)

        if show:
            self.show_figures()

    """
        Plot the original spectre
    """
    def plot_original_spectre(self, start, end=None, show=False):
        print('Preparing original spectre figure...')
        plt.figure(self.figure_n)    # create new figure
        self.figure_n += 1

        # if end value is set
        if end:
            # take columns from 'start' to 'end'
            spectre_slice = self.Pxx_DB[:, start:end][:]
        else:
            # else, just take column 'start'
            spectre_slice = self.Pxx_DB[:, start][:]

        # set y=spectre values, x=frequencies
        plt.plot(self.frequencies, spectre_slice)

        if show:
            self.show_figures()

    """
        Plot the modified spectre
    """
    def plot_modified_spectre(self, start, end=None, show=False):
        print('Preparing modified spectre figure...')
        plt.figure(self.figure_n)    # create new figure
        self.figure_n += 1

        # if end value is set
        if end:
            # take columns from 'start' to 'end'
            spectre_slice = self.Pxx_DB_modified[:, start:end]
        else:
            # else, just take column 'start'
            spectre_slice = self.Pxx_DB_modified[:, start]

        # set y=spectre values, x=frequencies
        plt.plot(self.frequencies, spectre_slice)

        if show:
            self.show_figures()

    """
        Plot figures of this plot
    """
    def show_figures(self):
        print('Showing figure(s)...')
        plt.show(block=False)
        input('Press any key to end the program...')
        plt.close('all')

    """
        Set all values of the spectrogram copy to 0 if they
        are below the mean value of the whole spectrogram. This
        value can be increased or decreased by altering the
        filter_coefficient.
    """
    def filter_by_mean(self, start, end=None, filter_coefficient=1):
        if end:
            # take columns from start to end if end is set
            spectrogram_slice = self.Pxx_DB_modified[:, start:end]
        else:
            # else just take start column
            spectrogram_slice = self.Pxx_DB_modified[:, start]

        spectrogram_slice_mean = np.mean(spectrogram_slice)

        # set all values below spectrogram_slice_mean * filter_coefficient to 0
        spectrogram_slice[
            spectrogram_slice < (spectrogram_slice_mean * filter_coefficient)
        ] = 0

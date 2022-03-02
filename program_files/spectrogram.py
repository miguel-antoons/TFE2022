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
        print(f'Signal length in frequency segments : {len(frequencies)}')
        print(f'Signal length in time segments : {len(times)}')
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
        fmin=0,
        fmax=None,
        show=False,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        title='Original Spectrogram'
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
            self.Pxx[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ]
        )

        # set graph and axis titles
        plt.ylabel(y_axis_title)
        plt.xlabel(x_axis_title)
        plt.title(title)

        if show:
            self.show_figures()

    """
        Plot the modified spectrogram
    """
    def plot_modified_spectrogram(
        self,
        fmin=0,
        fmax=None,
        show=False,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        title='Modified Spectrogram'
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

        # set graph and axis titles
        plt.ylabel(y_axis_title)
        plt.xlabel(x_axis_title)
        plt.title(title)

        if show:
            self.show_figures()

    """
        Plot the original spectre
    """
    def plot_original_spectre(
        self,
        start,
        end=None,
        fmin=0,
        fmax=None,
        show=False,
        xlabel='Frequency [Hz]',
        ylabel='Signal Strength [dB]',
        title='Original Spectre'
    ):
        # if fmax is not set, set default value
        if not fmax:
            fmax = self.sample_frequency / 2

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
        plt.plot(
            self.frequencies[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ],
            spectre_slice[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ]
        )

        # set graph and axis titles
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.title(title)

        if show:
            self.show_figures()

    """
        Plot the modified spectre
    """
    def plot_modified_spectre(
        self,
        start,
        end=None,
        fmin=0,
        fmax=None,
        show=False,
        xlabel='Frequency [Hz]',
        ylabel='Signal Strength [dB]',
        title='Modified Spectre'
    ):
        # if fmax is not set, set default value
        if not fmax:
            fmax = self.sample_frequency / 2

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
        plt.plot(
            self.frequencies[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ],
            spectre_slice[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ]
        )

        # set graph and axis titles
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.title(title)

        if show:
            self.show_figures()

    """
        Plot figures of this plot
    """
    def show_figures(self):
        print('Showing figure(s)...')
        plt.show(block=False)
        input('Press any key to end the program...')
        print('Closing figures...')
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

    def filter_with_kernel(
        self,
        start=0,
        end=None,
        kernel=np.array(
            [[0, 4/12, 0],
             [0, 1/12, 0],
             [1/6, 0, 1/6],
             [0, 1/12, 0],
             [0, 4/12, 0]],
            dtype=float
        ),
        coefficient=1
    ):
        """Function filters the copy of the spectrogram from column 'start' to
        column 'end' by performing a convolution witha kernel received as
        input.

        Args:
            start   (int, optional)         :   First column of the
                                                spectrogram. Defaults to 0.
            end     (int, optional)         :   Last column of the spectrogram.
                                                Defaults to None.
            kernel  (numpy.array, optional) :   The convolution kernel.
                                                Defaults to
                                                np.array(
                                                    [[1], [1], [0], [1], [1]],
                                                    dtype=float
                                                ).
        """
        if end:
            # take columns from start to end if end is set
            spectrogram_slice = self.Pxx_DB_modified[:, start:end]
        else:
            # else just take start column
            spectrogram_slice = self.Pxx_DB_modified[:, start]

        print("""
            Performing convolution between kernel and the copy
            of the spectrogram...
        """)
        print(f'Convolution kernel : \n{kernel}')
        print(f'Filter coefficient : {coefficient}')

        # performing convolution as many times as requested by the user
        for i in range(coefficient):
            spectrogram_slice = signal.convolve2d(
                spectrogram_slice, kernel, boundary='symm', mode='same'
            )

        print('Storing the convolution result...')
        if end:
            # take columns from start to end, if end is set
            # set filtered values
            self.Pxx_DB_modified[:, start:end] = spectrogram_slice
        else:
            # else just take start column and set new value
            self.Pxx_DB_modified[:, start] = spectrogram_slice

    def get_mean_value(self, rows_per_block=2731, cols_per_block=63):
        h, w = self.Pxx_DB.shape

        divised_pxx = self.Pxx.reshape(
                h//rows_per_block, rows_per_block, -1, cols_per_block
            ).swapaxes(1, 2).reshape(-1, rows_per_block, cols_per_block)

        previous_variance = None
        min_var_index = 0

        for index, pxx in enumerate(divised_pxx):
            variance = np.var(pxx, dtype=np.float64)
            print(variance)

            if not previous_variance or variance < previous_variance:
                previous_variance = variance
                min_var_index = index

        return np.mean(pxx[min_var_index])

    def retrieve_transmitter_signal(self):
        same_index = 0
        previous_index = 0
        index = 0
        while not same_index == 30:
            max_column_index = self.Pxx[:, index].argmax()
            print(max_column_index)

            if max_column_index == previous_index:
                same_index += 1

            previous_index = max_column_index
            index += 1

        return previous_index - 5, previous_index + 5

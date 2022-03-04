from scipy import signal, ndimage
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
        self.Pxx_DB_modified = self.subtract_transmitter_signal()
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
            self.Pxx_DB[
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
            np.copy(self.Pxx_DB_modified[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ])
        )

        # set graph and axis titles
        plt.ylabel(y_axis_title)
        plt.xlabel(x_axis_title)
        plt.title(title)

        if show:
            self.show_figures()

    def __get_slice(self, start, end, original_spectrogram=False):
        spectrogram = self.Pxx_DB_modified

        if original_spectrogram:
            spectrogram = self.Pxx_DB

        # if end value is set
        if end:
            # take columns from 'start' to 'end'
            return spectrogram[:, start:end]

        # else, just take column 'start'
        return spectrogram[:, start]

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

        spectre_slice = self.__get_slice(start, end, True)

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

        spectre_slice = self.__get_slice(start, end)

        # set y=spectre values, x=frequencies
        plt.plot(
            self.frequencies[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ],
            np.copy(spectre_slice[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ])
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
        spectrogram_slice = self.__get_slice(start, end)

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
            [[0, 6/12, 0],
             [0, 4/24, 0],
             [0, 2/24, 0],
             [0, 0, 0],
             [0, 2/24, 0],
             [0, 4/24, 0],
             [0, 6/12, 0]],
            dtype=float
        ),
        coefficient=1
    ):
        spectrogram_slice = self.__get_slice(start, end)
        spectrogram_slice_copy = np.copy(spectrogram_slice)

        print(
            'Performing convolution between kernel and the copy'
            'of the spectrogram...'
        )
        print(f'Convolution kernel : \n{kernel}')
        print(f'Filter coefficient : {coefficient}')

        # performing convolution as many times as requested by the user
        for i in range(coefficient):
            spectrogram_slice_copy = signal.convolve2d(
                spectrogram_slice_copy, kernel, boundary='symm', mode='same'
            )

        print('Storing the convolution result...')
        spectrogram_slice[:] = spectrogram_slice_copy

    def retrieve_transmitter_signal(self):
        same_index = 0
        previous_index = 0
        index = 0

        while not same_index == 30:
            max_column_index = self.Pxx[:, index].argmax()

            if max_column_index == previous_index:
                same_index += 1

            previous_index = max_column_index
            index += 1

        return previous_index - 2, previous_index + 2

    def subtract_transmitter_signal(self):
        start_row, end_row = self.retrieve_transmitter_signal()
        Pxx_copy = np.copy(self.Pxx_DB)

        for row in range(start_row, end_row):
            start_col = 0
            for end_col in range(3, Pxx_copy.shape[0], 3):
                normal_mean_value = (
                    np.mean(Pxx_copy[start_row - 1, start_col:end_col])
                    + np.mean(Pxx_copy[end_row + 1, start_col:end_col])
                ) / 2
                mean_value = np.mean(Pxx_copy[row, start_col:end_col])
                difference = mean_value - normal_mean_value
                Pxx_copy[row, start_col:end_col] -= difference
                start_col = end_col

        return Pxx_copy

    def binarize_slice(self, treshold, start=0, end=None):
        spectrogram_slice = self.__get_slice(start, end)

        spectrogram_slice[:] = np.where(spectrogram_slice > treshold, 1, 0)

    def delete_area(self, area_treshold, start=0, end=None):
        spectrogram_slice = self.__get_slice(start, end)

        labeled_spectrogram, num_labels = ndimage.label(spectrogram_slice)
        objects = ndimage.find_objects(labeled_spectrogram)

        for object in objects:
            height, width = spectrogram_slice[object].shape

            if height < 15:
                spectrogram_slice[object] = 0

        spectrogram_slice[:] = ndimage.binary_dilation(
            spectrogram_slice, iterations=2
        )
        spectrogram_slice[:] = np.where(spectrogram_slice > 0, 100, 0)

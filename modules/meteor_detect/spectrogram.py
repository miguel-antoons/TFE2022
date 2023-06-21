import numpy as np
import matplotlib.pyplot as plt
import math

from scipy import signal, ndimage


class Spectrogram:
    """
    This class generates a spectrogram form an audio signal. It also contains
    a load of methods capable of performing actions on that spectrogram such
    as :
        - labelisation
        - binarization
        - meteor signal retrieval
        - ...
    """
    def __init__(
        self,
        audio_signal,
        nfft=16384,
        sample_frequency=5512,
        noverlap=14488,
        window='hamming',
        max_normalization=1
    ):
        """
        Function prepares the class and initializes all of its properties.
        It also generates the spectrogram from the given wav file

        Parameters
        ----------
        audio_signal : BramsWavFile
            wav from which to calculate the spectrogram
        nfft : int, optional
            nfft of the generated spectrogram, by default 16384
        sample_frequency : int, optional
            sample frequency of the given wav file, by default 5512
        noverlap : int, optional
            overlap of the generated spectrogram, by default 14488
        window : str, optional
            type of window used to generate the spectrogram
            , by default 'hamming'
        max_normalization : int, optional
            maximum value after spectrogram normalization, by default 1
        """
        # generate the spectrogram from the init funtion arguments
        self.frequencies, self.times, Pxx = signal.spectrogram(
            audio_signal,
            sample_frequency,
            nperseg=nfft,
            noverlap=noverlap,
            window=window,
        )

        self.frequency_resolution = (
            sample_frequency / 2 / len(self.frequencies)
        )

        self.sample_frequency = sample_frequency

        # normalize the spectrogram
        Pxx = self.__normalize_spectrogram(max_normalization, Pxx)
        # spectrogram in dB
        self.Pxx_DB = 10. * np.log10(Pxx)
        # retrieve the frequency of the transmitter signal
        (
            self.start_transmitter_row,
            self.end_transmitter_row,
            self.max_transmitter_row
        ) = self.__retrieve_transmitter_signal(Pxx)
        # create a copy and subtract the transmitter signal
        self.Pxx_modified = self.__subtract_transmitter_signal(Pxx)

        # initialize the figure number to 1
        self.figure_n = 1

        self._default_treshold = None

    @property
    def __default_treshold(self):
        """
        Represents the default noise threshold

        Returns
        -------
        float
            default noise threshold
        """
        if self._default_treshold is None:
            self._default_treshold = self.__find_noise_value()

        return self._default_treshold

    def __normalize_spectrogram(self, max_normalization, Pxx):
        """
        Function generates a normalized version of the spectrogram

        Parameters
        ----------
        max_normalization : float
            max value of the normalized spectrogram
        Pxx : np.array
            spectrogram to normalize

        Returns
        -------
        np.array
            normalized spectrogram
        """
        max_pxx = np.max(Pxx)

        Pxx = Pxx / max_pxx * max_normalization

        return Pxx

    def plot_original_spectrogram(
        self,
        interval=1000,
        show=False,
        show_all=False,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        title='Original Spectrogram'
    ):
        """
        Plot the original spectrogram contained by this class

        Parameters
        ----------
        interval : int, optional
            interval in Hz of the spectrogram to show, by default 1000
        show : bool, optional
            defines wether to show the plot directly or not, by default False
        show_all : bool, optional
            wether to show the whole spectrogram or not (overrides interval
            argument), by default False
        x_axis_title : str, optional
            title of the x axis, by default 'Time [sec]'
        y_axis_title : str, optional
            title of the y axis, by default 'Frequency [Hz]'
        title : str, optional
            title of the plot, by default 'Original Spectrogram'
        """
        # increase the interval if the direct signal is unknown
        if (
            not self.start_transmitter_row
            and interval < (len(self.frequencies) - 200)
        ):
            interval += 200

        # if show_all is set, show the whole spectrogram
        if show_all:
            fmin = 0
            fmax = self.sample_frequency / 2
        else:
            fmin = (
                (self.max_transmitter_row * self.frequency_resolution)
                - (interval / 2)
            )
            fmax = (
                (self.max_transmitter_row * self.frequency_resolution)
                + (interval / 2)
            )

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
            self.__show_figures()

    def plot_modified_spectrogram(
        self,
        interval=1000,
        show_all=False,
        show=False,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        title='Modified Spectrogram'
    ):
        """
        plot the modified spectrogram contained by this class

        Parameters
        ----------
        interval : int, optional
            frequency interval from the modified spectrogram to show
            , by default 1000
        show_all : bool, optional
            indicates if the user wants to plot the whole spectrogram or not
            (overrides interval argument), by default False
        show : bool, optional
            indicates if the generated plot has to be shown right away or not
            , by default False
        x_axis_title : str, optional
            title of the x axis, by default 'Time [sec]'
        y_axis_title : str, optional
            title of the y axis, by default 'Frequency [Hz]'
        title : str, optional
            title of the spectrogram plot, by default 'Modified Spectrogram'
        """
        # increase the interval if the direct signal is unknown
        if (
            not self.start_transmitter_row
            and interval < (len(self.frequencies) - 200)
        ):
            interval += 200

        # if show_all is set then override the fmin and fmax values in order
        # to show the whole spectrogram
        if show_all:
            fmin = 0
            fmax = self.sample_frequency / 2
        else:
            fmin = (
                (self.max_transmitter_row * self.frequency_resolution)
                - (interval / 2)
            )
            fmax = (
                (self.max_transmitter_row * self.frequency_resolution)
                + (interval / 2)
            )

        # show the spectrogram in dB units
        Pxx_DB_modified = 10. * np.log10(self.Pxx_modified)

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
            np.copy(Pxx_DB_modified[
                (self.frequencies >= fmin) & (self.frequencies <= fmax)
            ])
        )

        # set graph and axis titles
        plt.ylabel(y_axis_title)
        plt.xlabel(x_axis_title)
        plt.title(title)

        if show:
            self.__show_figures()

    def __get_slice(
        self,
        start,
        end,
        original_spectrogram=False,
        get_copy=False
    ):
        """
        Function returns a slice from one of the 2 spectrograms contained in
        this class

        Parameters
        ----------
        start : int
            start column of the spectrogram slice
        end : int
            end column of the spectrogram slice
        original_spectrogram : bool, optional
            indicates wether a slice has to be taken from the original or
            modified spectrogram, by default 0
        get_copy : bool, optional
            wether to get an actual slice of the spectrogram or a copy from
            that slice, by default False

        Returns
        -------
        np.array
            requested slice of the requested spectrogram
        """
        spectrogram = self.Pxx_modified

        # if the start index is below the spectrogram start
        if start < 0:
            start = 0

        # if end value is set
        if end is None:
            end = start + 1

        # if the end value goes farther than the last spectrogram value
        if end >= len(self.times):
            # set the end value to the last possible spectrogram index
            end = len(self.times) - 1

        if original_spectrogram:
            spectrogram = self.Pxx_DB

        # take columns from 'start' to 'end'
        spectrogram = spectrogram[:, start:end]

        if get_copy:
            return spectrogram.copy()

        return spectrogram

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
        """
        Function plots the spectre of the original spectrogram.

        Parameters
        ----------
        start : int
            start column of the spectrogram to show the spectre of
        end : int, optional
            end column of the spectrogram to show the spectre of
            , by default None
        fmin : int, optional
            minimum frequency to show on the spectre, by default 0
        fmax : int, optional
            maximum frequency to show on the spectre, by default None
        show : bool, optional
            wether to show the spectre plot right away or not, by default False
        xlabel : str, optional
            x axis label, by default 'Frequency [Hz]'
        ylabel : str, optional
            y axis label, by default 'Signal Strength [dB]'
        title : str, optional
            plot title, by default 'Original Spectre'
        """
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
            self.__show_figures()

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
        """
        function plots the spectre of a slice of the modified spectrogram
        contained by this class.

        Parameters
        ----------
        start : int
            start column of the spectrogram to show the spectre of
        end : int, optional
            end column of the spectrogram to show the spectre of
            , by default None
        fmin : int, optional
            minimum frequency shown on the spectre, by default 0
        fmax : int, optional
            maximum frequency shown on the spectre, by default None
        show : bool, optional
            wether to show the spectre plot right away or not, by default False
        xlabel : str, optional
            x axis label, by default 'Frequency [Hz]'
        ylabel : str, optional
            y axis label, by default 'Signal Strength [dB]'
        title : str, optional
            plot title, by default 'Modified Spectre'
        """
        # if fmax is not set, set default value
        if not fmax:
            fmax = self.sample_frequency / 2

        print('Preparing modified spectre figure...')
        plt.figure(self.figure_n)    # create new figure
        self.figure_n += 1

        spectre_slice = 10. * np.log10(self.__get_slice(start, end))

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
            self.__show_figures()

    def __show_figures(self):
        """
        function shows all the generated plots.
        After the plots are generated it waits for a user input to close the
        plots
        """
        print('Showing figure(s)...')
        plt.show(block=False)
        input('Press any key to close the figures...')
        print('Closing figures...')
        plt.close('all')

    def filter_low(self, min_value=None, start=0, end=None, filter_all=False):
        """
        * currently not used
        Function filters all the values lower than a given value in the
        spectrogram slice

        Parameters
        ----------
        min_value : float, optional
            treshold, all the values below this value will be filtered
            , by default None
        start : int, optional
            start column of the spectrogram slice, by default 0
        end : int, optional
            end column of the spectrogram slice, by default None
        filter_all : bool, optional
            wether to filter the whole spectrogram instead of just a slice
            (overrides start and end arguments if set to True)
            , by default False
        """
        # if no treshold is given, set a default treshold
        if min_value is None:
            min_value = self.__default_treshold()

        if filter_all:
            start = 0
            end = len(self.times) - 1

        spectrogram_slice = self.__get_slice(start, end)

        # set all values below the noise treshold to 0.000001
        spectrogram_slice[
            spectrogram_slice < min_value
        ] = 0.000001

    def filter_with_kernel(
        self,
        start=0,
        end=None,
        filter_all=False,
        kernel=np.array(
            [[0, 1/3, 0],
             [0, 1/3, 0],
             [0, 1/3, 0]],
            dtype=float
        ),
        coefficient=1
    ):
        """
        Function filters a spectrogram slice with a given filter and applies
        this filter with a convolution

        Parameters
        ----------
        start : int, optional
            start column of the slice to filter, by default 0
        end : int, optional
            end of the spectrogram slice to filter, by default None
        filter_all : bool, optional
            wether to filter the whole spectrogram (overrides the start and
            end argument if set to True), by default False
        kernel : np.array, optional
            convolution kernel to filter the spectrogram with
            , by default np.array(
                [[0, 1/3, 0],
                 [0, 1/3, 0],
                 [0, 1/3, 0]]
                , dtype=float
            )
        coefficient : int, optional
            number of times the filter has to be applied, by default 1
        """
        if filter_all:
            spectrogram_slice = self.Pxx_modified
            spectrogram_slice_copy = self.Pxx_modified.copy()
        else:
            spectrogram_slice = self.__get_slice(start, end)
            spectrogram_slice_copy = np.copy(spectrogram_slice)

        # performing convolution as many times as requested by the user
        for i in range(coefficient):
            spectrogram_slice_copy = ndimage.convolve(
                spectrogram_slice_copy,
                kernel,
                mode='constant'
            )

        # print('Storing the convolution result...')
        spectrogram_slice[:] = spectrogram_slice_copy

    def __retrieve_transmitter_signal(self, Pxx, fmin=800, fmax=1200):
        """
        Function tries to retrieve the frequency(ies) of the transmitter
        signal.
        If the transmitter signal was not found, it returns 1000Hz.

        Parameters
        ----------
        Pxx : np.array
            spectrogram on which the function will try to find the transmitter
            frequency(ies)
        fmin : int, optional
            minimum frequency above which to search for the transmitter signal
            , by default 800
        fmax : int, optional
            maximum frequency below which to search for the transmitter signal
            , by default 1200

        Returns
        -------
        tuple
            the upper, middle and lower frequency of the transmitter signal
        """
        same_index = 0
        previous_index = 0
        index = 0
        min_row = round(fmin / self.frequency_resolution)
        max_row = round(fmax / self.frequency_resolution)

        # while there is no row that has the highest value for 50 columns
        while not same_index == 50 and index < len(self.times):
            # find highest row value of a column
            max_column_index = Pxx[min_row:max_row, index].argmax()

            # check if it is close or the same frequency as the previous
            # highest value
            if max_column_index in [
                previous_index - 1, previous_index, previous_index + 1
            ]:
                same_index += 1
            else:
                same_index = 0
                previous_index = max_column_index

            index += 1

        # if no transmitter signal was found
        if same_index < 50:
            # print(
            #     'Direct signal was not found, spectrogram will be '
            #     'shown around default value of 1000 Hz.'
            # )
            return False, False, round(1000 / self.frequency_resolution)

        # print(
        #     'Direct signal was found around '
        #     f'{(previous_index + min_row) * self.frequency_resolution} Hz.'
        # )
        return (
            (previous_index + min_row - 2),
            (previous_index + min_row + 3),
            (previous_index + min_row)
        )

    def __subtract_transmitter_signal(self, Pxx):
        """
        Function tries to eliminate the transmitter signal from a given
        spectrogram

        Parameters
        ----------
        Pxx : np.array
            spectrogram to delete the transmitter signal from

        Returns
        -------
        np.array
            the spectrogram without the transmitter signal
        """
        # check if the transmitter signal's frequency is known
        if self.start_transmitter_row:
            # replace all the transmitter values with the values from the
            # upper and lower frequencies
            for row in range(
                self.start_transmitter_row, self.end_transmitter_row + 1
            ):
                start_col = 0
                for end_col in range(3, Pxx.shape[0], 3):
                    normal_mean_value = (
                        np.mean(Pxx[
                            self.start_transmitter_row - 1, start_col:end_col
                        ])
                        + np.mean(Pxx[
                            self.end_transmitter_row + 1, start_col:end_col
                        ])
                    ) / 2

                    Pxx[row, start_col:end_col] = normal_mean_value
                    start_col = end_col

            Pxx[Pxx <= 0] = 0.001

        return Pxx

    def __binarize_slice(self, treshold, start=0, end=None, spectrogram=None):
        """
        Function binarizes a slice of the spectrogram contained by this class.
        It then returns that binarized slice.

        Parameters
        ----------
        treshold : float
            binarization treshold
        start : int, optional
            start of the spectrogram slice, by default 0
        end : int, optional
            end of the spectrogram slice, by default None
        spectrogram : np.array, optional
            alternative spectrogram to binarize a slice from, by default None

        Returns
        -------
        np.array
            new spectrogram with binarized slice
        """
        if spectrogram is None:
            spectrogram = self.__get_slice(start, end)
        return np.where(spectrogram > treshold, 1, 0)

    def delete_area(
        self,
        area_treshold,
        start=0,
        end=None,
        delete_all=False,
        get_copy=False,
        spectrogram=None
    ):
        """
        Function deletes all objects of a  spectrogram slice if the height of
        those objects is smaller than a given treshold.
        If necessary, it returns a copy of the spectrogram without the small
        objects.

        Parameters
        ----------
        area_treshold : int
            height area treshold
        start : int, optional
            start of the spectrogram slice, by default 0
        end : int, optional
            end of the spectrogram slice, by default None
        delete_all : bool, optional
            wether to delete objects from the whole spectrogram (overrides
            start and end arguments if set to True), by default False
        get_copy : bool, optional
            if set to True, the function returns a copy of the spectrogram
            without the small objects, by default False
        spectrogram : np.array, optional
            spectrogram to delete small objects from, by default None

        Returns
        -------
        np.array
            copy of the spectrogram without small objects (only if get_copy is
            set to True)
        """
        if delete_all:
            start = 0
            end = len(self.times)

        # if no spectrogram is specified, take the spectrogram contained by
        # this class
        if spectrogram is None:
            spectrogram_slice = self.__get_slice(start, end)
        else:
            spectrogram_slice = spectrogram

        if get_copy:
            spectrogram_slice = spectrogram_slice.copy()

        # get all the objects within the slice
        objects = self.__get_object_coords(start, end)

        # for each object
        for object in objects:
            height, width = spectrogram_slice[object].shape

            # if the height of the object is smaller than the treshold
            if height < area_treshold:
                # lower the value of that object
                spectrogram_slice[object] = 0.0000001

        if get_copy:
            return spectrogram_slice

    def __create_blocks(self, height=3, width=10, fmin=600, fmax=1400):
        # * currently not used
        Pxx_copy = np.copy(self.Pxx_modified[
            (self.frequencies >= fmin) & (self.frequencies <= fmax)
        ])
        h, w = Pxx_copy.shape

        height_surplus = h % height
        width_surplus = w % width

        if height_surplus:
            Pxx_copy = Pxx_copy[:-height_surplus]
        if width_surplus:
            Pxx_copy = Pxx_copy[:, :-width_surplus]

        h, w = Pxx_copy.shape

        row_per_block = h // height
        col_per_block = w // width

        return (
            Pxx_copy
            .reshape(h // row_per_block, row_per_block, -1, col_per_block)
            .swapaxes(1, 2)
            .reshape((height * width), row_per_block, col_per_block)
        )

    def __find_noise_value(self):
        # * currently not used
        pxx_blocks = self.__create_blocks()
        block_info = []

        for index, block in enumerate(pxx_blocks):
            block_info.append({
                'variance': np.var(block),
                'percentile_95': np.percentile(block, 95),
                'index': index,
            })

        all_var_median = np.median([block['variance'] for block in block_info])

        block_info = [
            block for block in block_info if block['variance'] < all_var_median
        ]

        max_percentile = np.max(
            [block['percentile_95'] for block in block_info]
        )

        block_info = [
            block for block in block_info
            if block['percentile_95'] == max_percentile
        ]
        used_block = pxx_blocks[block_info[0]['index']]

        # min_max_objective = 0.05 * (used_block.max() - used_block.mean())
        # print(f'Min max objective : {min_max_objective}')

        # while (used_block.max() - used_block.mean()) > min_max_objective:
        #     used_block = signal.convolve2d(
        #         used_block, kernel, boundary='symm', mode='same'
        #     )
        #     print('hello')
        used_block = signal.convolve2d(
                used_block,
                np.full((5, 5), 1 / 25),
                boundary='symm',
                mode='same'
            )
        # flat_used_block = used_block.flatten()
        # return block_info[0]['percentile_95']
        percentile = np.percentile(used_block, 97)

        return percentile
        # return (
        #     stats.t.interval(
        #         0.95,
        #         len(flat_used_block) - 1,
        #         loc=np.mean(flat_used_block),
        #         scale=stats.sem(flat_used_block)
        #     )[1]
        # )

    def filter_by_percentile(
        self,
        start=0,
        end=None,
        filter_all=False,
        percentile=95
    ):
        """
        function filters all the columns within a given slice of the
        spectrogram contained by this class by their given percentiles.

        Parameters
        ----------
        start : int, optional
            start of the spectrogram slice, by default 0
        end : int, optional
            end of the spectrogram slice, by default None
        filter_all : bool, optional
            if set, filters the whole spectrogram (overrides start and end
            argument if set to True), by default False
        percentile : int, optional
            percentile below which values will be filtered, by default 95
        """
        if filter_all:
            spectrogram_slice = self.Pxx_modified
        else:
            spectrogram_slice = self.__get_slice(start, end)

        # for each column of the given slice
        for column in spectrogram_slice.T:
            # get the percentile
            column_percentile = np.percentile(column, percentile)
            # filter all the values below that percentile
            column[column < column_percentile] = 0.001

    def get_potential_meteors(
        self,
        start=0,
        end=None,
        get_all=False,
        broad_start=None,
        broad_end=None
    ):
        """
        Function tries to detect meteors on a given spectrogram slice.
        It returns the structured coordinates of the found meteors.

        Parameters
        ----------
        start : int, optional
            start of the slice to search, by default 0
        end : int, optional
            end of the slice to search, by default None
        get_all : bool, optional
            indicates if the whole spectrogram has to be searched (overrides
            start, end, broad_start and broad_end arguments if set to True)
            , by default False
        broad_start : int, optional
            start of the slice from where plane detections can be found
            , by default None
        broad_end : int, optional
            end of the slice upto where plane detections can be found
            , by default None

        Returns
        -------
        list
            list of objects. Each object contains info of a detected meteor
        """
        pot_meteors = []

        # if the users wants the meteors on the whole spectrogram
        if get_all:
            start = 0
            end = len(self.times)
            broad_start = 0
            broad_end = end

        if start < 0:
            start = 0

        if broad_start is None:
            broad_start = start

        if broad_end is None:
            broad_end = end

        broad_spectrogram = self.__get_slice(broad_start, broad_end)
        pxx_copy = self.Pxx_modified.copy()

        # for each column delete objects of small height
        for i in range(len(broad_spectrogram.T)):
            self.delete_area(
                10 / self.frequency_resolution,
                start=(i + broad_start)
            )

        # get all the objects from the slice to search (from start to end)
        object_coords = self.__get_object_coords(
            start=start,
            end=end,
            get_all=get_all,
        )

        # iterate over all the spectrogram objects
        for object in object_coords:
            total_width = 0
            # start and stop of the area around the detected meteor to search
            # for plane echoes
            detection_start = (object[1].start - 22 + start)
            detection_stop = (object[1].stop + 22 + start)
            fmax = object[0].stop + 3
            fmin = object[0].start - 3
            pot_meteor_height = object[0].stop - object[0].start
            pot_meteor_width = object[1].stop - object[1].start

            if detection_start < 0:
                detection_start = 0

            if detection_stop > len(self.times):
                detection_stop = len(self.times) - 1

            # if the object is found below 800 Hz or above 1400Hz it si highly
            # unlikely to be a meteor
            if (
                self.frequencies[object[0].start] < 800
                or self.frequencies[object[0].stop] > 1400
            ):
                continue
            # if the object is higher than 60 and smaller than 6, it is highly
            # likely to be a meteor
            elif pot_meteor_width < 6 and pot_meteor_height > 50:
                # consider the object as a meteor
                pot_meteors.append((
                    object[0],
                    slice(
                        object[1].start + start,
                        object[1].stop + start,
                        None
                    )
                ))

            # if the object is wider than 1
            elif pot_meteor_width > 1:
                column = object[1].start - 1 + start
                no_objects = 0
                # iterate over the 20 columns coming before the start of the
                # current object. This is done in order to detect plan echoes
                while (
                    column > detection_start
                    and no_objects <= 2
                    and total_width < 16
                ):
                    # get all the objects from the current column
                    column_objects = self.__get_object_coords(
                        # spectrogram=self.Pxx_modified[fmin:fmax, column]
                        spectrogram=pxx_copy[fmin:fmax, column]
                    )

                    # if there are any objects
                    if len(column_objects):
                        slice_object = column_objects[0][0]

                        # if there are several objects
                        if len(column_objects) > 1:
                            fstart = 0
                            fstop = -4

                            # check if all those objects lay close to each
                            # other or not
                            for column_object in column_objects:
                                max_gap = 0.25 * (fmax - fmin)

                                # check if 2 objects lay close or far form each
                                # other
                                if column_object[0].start > (fstop + max_gap):
                                    # if they lay far from each other, reset
                                    # the start
                                    fstart = column_object[0].start

                                # set new stop
                                fstop = column_object[0].stop

                            slice_object = slice(fstart, fstop, None)

                        no_objects += 1
                        # if the objects next to the detected meteor are
                        # almost as big as the meteor itself
                        if (
                            (slice_object.stop - slice_object.start)
                            > ((fmax - fmin) * 0.7)
                        ):
                            if no_objects > 0:
                                no_objects -= 2
                            total_width += 1
                            fmax = fmin + slice_object.stop + 3
                            fmin += slice_object.start - 3
                    else:
                        no_objects += 1
                    column -= 1

                column = object[1].stop + 1 + start
                no_objects = 0

                fmax = object[0].stop + 3
                fmin = object[0].start - 3

                # iterate over the 20 columns coming after the stop of the
                # current object. This is done to detect plane echoes.
                while (
                    column < detection_stop
                    and no_objects <= 2
                    and total_width < 16
                ):
                    # get all the objects of the current column
                    column_objects = self.__get_object_coords(
                        spectrogram=pxx_copy[fmin:fmax, column]
                    )

                    # if there is an object found
                    if len(column_objects):
                        slice_object = column_objects[0][0]

                        # if there are several objects
                        if len(column_objects) > 1:
                            fstart = 0
                            fstop = -4

                            # check if those objects lay close to each other
                            for column_object in column_objects:
                                max_gap = 0.25 * (fmax - fmin)

                                # check if 2 objects lay clos or far form each
                                # other
                                if column_object[0].start > (fstop + max_gap):
                                    # if they lay far from each other, reset
                                    # the start
                                    fstart = column_object[0].start

                                # set new stop
                                fstop = column_object[0].stop

                            slice_object = slice(fstart, fstop, None)

                        no_objects += 1
                        # if the object is almost as big as the detected meteor
                        if (
                            (slice_object.stop - slice_object.start)
                            > ((fmax - fmin) * 0.7)
                        ):
                            if no_objects > 0:
                                no_objects -= 2
                            total_width += 1
                            fmax = fmin + slice_object.stop + 3
                            fmin += slice_object.start - 3
                    else:
                        no_objects += 1
                    column += 1

                # if the width of the objects is eventually less than 16
                # , consider it being a meteor
                if total_width < 16:
                    pot_meteors.append((
                        object[0],
                        slice(
                            object[1].start + start,
                            object[1].stop + start,
                            None
                        )
                    ))

        # * below code is for debugging purposes only
        # for meteor in pot_meteors:
        #     self.Pxx_modified[meteor] = 100000000

        # get all the structured meteor coordinates and return the results
        return self.__get_structured_meteor_coords(pot_meteors)

    def __get_object_coords(
        self,
        start=0,
        end=None,
        get_all=False,
        treshold=0.01,
        spectrogram=None
    ):
        """
        Function retrieves objects within a slice of a spectrogram, it then
        returns all the coordinates of the found objects

        Parameters
        ----------
        start : int, optional
            start of the slice to search, by default 0
        end : int, optional
            end of the slice to search, by default None
        get_all : bool, optional
            if set, get objects from the whole spectrogram (overrides start
            and end arguments of set to True), by default False
        treshold : float, optional
            binarization treshold, by default 0.01
        spectrogram : np.array, optional
            spectrogram on which to search objects, by default None

        Returns
        -------
        array
            array with the coordinates of all the found objects
        """
        if get_all:
            start = 0
            end = len(self.times)

        # binarize the spectrogram slice
        bin_spectrogram_slice = self.__binarize_slice(
            treshold, start, end, spectrogram
        )

        # label the binary spectrogram slice
        labeled_spectrogram, num_labels = ndimage.label(bin_spectrogram_slice)
        # return all the coordinates of the found objects
        return ndimage.find_objects(labeled_spectrogram)

    def __get_structured_meteor_coords(self, meteor_slices):
        """
        Function generates structures meteor coordinates from meteors slices
        on the spectrogram.
        Each meteors will have a t_start and t_stop in seconds and a fmin and
        fmax in Hz. It will also return the slice of the meteor.

        Parameters
        ----------
        meteor_slices : list
            list of meteor slices

        Returns
        -------
        list
            list with the structures meteor coordinates
        """
        meteor_coords = []

        for meteor_slice in meteor_slices:
            meteor_coords.append({
                't_start': self.times[meteor_slice[1].start] * 1000000,
                't_stop': self.times[meteor_slice[1].stop] * 1000000,
                'f_min': self.frequencies[meteor_slice[0].start],
                'f_max': self.frequencies[meteor_slice[0].stop],
                't_slice': meteor_slice[1],
                'f_slice': meteor_slice[0]
            })

        return meteor_coords

    def get_meteor_specs(self, meteor_coords):
        """
        Function tries gets a list of meteor coordinates and tries to find
        their lower and upper frequencies as precise as possible, it then adds
        those values to the list it's received and returns the updated meteor
        coordinates list.

        Parameters
        ----------
        meteor_coords : list
            list with all the meteor coordinates

        Returns
        -------
        list
            update list with the frequency extremities
        """
        for meteor_info in meteor_coords:
            # generate an fft of the found meteor's column
            fft_slice = np.zeros(len(self.frequencies))
            for i in range(
                meteor_info['t_slice'].start,
                meteor_info['t_slice'].stop
            ):
                fft_slice += self.Pxx_DB[:, i]

            # filter all values below the 85th percentile of the fft
            noise_percentile = np.percentile(fft_slice, 85)
            min_value = fft_slice.min()
            fft_slice[fft_slice <= noise_percentile] = min_value

            # set the boundaries for finding upper and lower frequency
            min_value_count = 0
            slice_start_index = (
                meteor_info['f_slice'].start
                + math.floor(
                    (
                        meteor_info['f_slice'].stop
                        - meteor_info['f_slice'].start
                    ) / 2
                )
            )
            slice_stop_index = (
                meteor_info['f_slice'].start
                + math.ceil(
                    (
                        meteor_info['f_slice'].stop
                        - meteor_info['f_slice'].start
                    ) / 2
                )
            )
            # searching start (fmin) value
            while min_value_count < 2 and slice_start_index > 0:
                if fft_slice[slice_start_index] == min_value:
                    min_value_count += 1
                elif min_value > 0:
                    min_value_count -= 1

                slice_start_index -= 1

            min_value_count = 0
            # searching stop (fmax) value
            while (
                min_value_count < 2
                and slice_stop_index < len(self.frequencies)
            ):
                if fft_slice[slice_stop_index] == min_value:
                    min_value_count += 1
                elif min_value > 0:
                    min_value_count -= 1

                slice_stop_index += 1

            # add the values to the meteor coordinates list
            meteor_info['f_min'] = self.frequencies[slice_start_index - 1]
            meteor_info['f_max'] = self.frequencies[slice_stop_index - 1]
            meteor_info['t'] = self.times[(
                meteor_info['t_slice'].start
                + round(
                    (
                        meteor_info['t_slice'].stop
                        - meteor_info['t_slice'].start
                    ) / 2
                )
            )]

        return meteor_coords

    def increase_object_value(
        self,
        start=0,
        end=None,
        get_all=False
    ):
        """
        Function increases the value of objects within a slice that find
        themselves above a given treshold and are grater than a certain size.

        Parameters
        ----------
        start : int, optional
            start of the spectrogram slice, by default 0
        end : int, optional
            end of the spectrogram slice, by default None
        get_all : bool, optional
            is set, apply this function's effect on the whole spectrogram
            (overrides start and en arguments if set to True), by default False
        """
        if get_all:
            start = 0
            end = len(self.times)

        if start < 0:
            start = 0

        spectrogram_slice = self.__get_slice(start, end)

        for i in range(len(spectrogram_slice.T)):
            # get objects above the treshold
            object_coords = self.__get_object_coords(
                start=i + start,
                get_all=False,
                treshold=0.002,
            )

            # if the objects are higher than 12 rows, increase their value
            for coords in object_coords:
                if (coords[0].stop - coords[0].start) > 12:
                    coords_corrected = (
                        coords[0],
                        slice(i + start, i + start + 1, None)
                    )
                    self.Pxx_modified[coords_corrected] = 10

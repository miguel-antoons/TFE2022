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
        window='hamming',
        max_normalization=100000
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
        print(f'Linear singal values go from 0 to {max_normalization}')

        self.frequency_resolution = sample_frequency / 2 / len(frequencies)
        # sample frequency of the wav audio signal
        self.sample_frequency = sample_frequency
        # frequencies contained by the audio signal
        self.frequencies = np.frombuffer(frequencies, dtype=float)
        # time segments contained in the audio signal
        self.times = np.frombuffer(times, dtype=float)
        # signal strength
        self.Pxx = self.__normalize_spectrogram(max_normalization, Pxx)
        # signal strength in dB
        self.Pxx_DB = 10. * np.log10(self.Pxx)
        # TODO : comments
        (
            self.start_transmitter_row,
            self.end_transmitter_row,
            self.max_transmitter_row
        ) = self.__retrieve_transmitter_signal()
        # copy of the signal strencgth in dB to be modified
        self.Pxx_modified = self.__subtract_transmitter_signal()
        # initialize the figure number to 1
        self.figure_n = 1

        self.default_treshold = self.find_noise_mean()

        print(f'Default treshold value : {self.default_treshold}')

        # DEVELOP
        print(f'Max spectrogram value : {np.max(self.Pxx)}')
        print(f'Min spectrogram value : {np.min(self.Pxx)}')

    def __normalize_spectrogram(self, max_normalization, Pxx):
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
        if (
            not self.start_transmitter_row
            and interval < (len(self.frequencies) - 200)
        ):
            interval += 200

        # if fmax is not set, set default value
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
            self.show_figures()

    def plot_modified_spectrogram(
        self,
        interval=1000,
        show_all=False,
        show=False,
        x_axis_title='Time [sec]',
        y_axis_title='Frequency [Hz]',
        title='Modified Spectrogram'
    ):
        if (
            not self.start_transmitter_row
            and interval < (len(self.frequencies) - 200)
        ):
            interval += 200

        # if fmax is not set, set default value
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
            self.show_figures()

    def __get_slice(self, start, end, original_spectrogram=0, get_copy=False):
        spectrogram = self.Pxx_modified

        if original_spectrogram == 1:
            spectrogram = self.Pxx_DB

        # if end value is set
        if end:
            # take columns from 'start' to 'end'
            spectrogram = spectrogram[:, start:end]
        else:
            # else, just take column 'start'
            spectrogram = spectrogram[:, start:start + 1]

        if get_copy:
            return spectrogram.copy()

        return spectrogram

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
    def filter_low(self, min=None, start=0, end=None, filter_all=False,):
        if not min:
            min = self.default_treshold

        if filter_all:
            end = len(self.times - 1)

        spectrogram_slice = self.__get_slice(start, end)

        # set all values below spectrogram_slice_mean * filter_coefficient to 0
        spectrogram_slice[
            spectrogram_slice < min
        ] = 1

    def filter_high(
        self,
        coefficient=1,
        start=0,
        end=None,
        filter_all=False,
        custom_value=0
    ):
        if filter_all:
            end = len(self.times - 1)

        if custom_value:
            max = custom_value
        else:
            max = (
                (coefficient / 10)
                * np.mean(self.Pxx[self.max_transmitter_row])
            )

        spectrogram_slice = self.__get_slice(start, end)

        # set all values below spectrogram_slice_mean * filter_coefficient to 0
        spectrogram_slice[
            spectrogram_slice > max
        ] = 1

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
        if filter_all:
            spectrogram_slice = self.Pxx_modified
            spectrogram_slice_copy = self.Pxx_modified.copy()
        else:
            spectrogram_slice = self.__get_slice(start, end)
            spectrogram_slice_copy = np.copy(spectrogram_slice)

        # print(
        #     'Performing convolution between kernel and the copy'
        #     'of the spectrogram...'
        # )
        # print(f'Convolution kernel : \n{kernel}')
        # print(f'Filter coefficient : {coefficient}')

        # performing convolution as many times as requested by the user
        for i in range(coefficient):
            spectrogram_slice_copy = signal.convolve2d(
                spectrogram_slice_copy, kernel, boundary='symm', mode='same'
            )

        # print('Storing the convolution result...')
        spectrogram_slice[:] = spectrogram_slice_copy

    def __retrieve_transmitter_signal(self, fmin=800, fmax=1200):
        same_index = 0
        previous_index = 0
        index = 0
        min_row = round(fmin / self.frequency_resolution)
        max_row = round(fmax / self.frequency_resolution)

        print(f'Searching direct signal between {fmin} Hz and {fmax} Hz...')

        while not same_index == 50 and index < len(self.times):
            max_column_index = self.Pxx[min_row:max_row, index].argmax()
            print(index)

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
            return False, False, round(1000 / self.frequency_resolution)

        print(
            'Direct signal was found around '
            f'{(previous_index + min_row) * self.frequency_resolution} Hz.'
        )
        return (
            (previous_index + min_row - 2),
            (previous_index + min_row + 3),
            (previous_index + min_row)
        )

    def __subtract_transmitter_signal(self):
        Pxx_copy = np.copy(self.Pxx)

        if self.start_transmitter_row:
            for row in range(
                self.start_transmitter_row, self.end_transmitter_row + 1
            ):
                start_col = 0
                for end_col in range(3, Pxx_copy.shape[0], 3):
                    normal_mean_value = (
                        np.mean(Pxx_copy[
                            self.start_transmitter_row - 1, start_col:end_col
                        ])
                        + np.mean(Pxx_copy[
                            self.end_transmitter_row + 1, start_col:end_col
                        ])
                    ) / 2

                    Pxx_copy[row, start_col:end_col] = normal_mean_value
                    start_col = end_col

            Pxx_copy[Pxx_copy <= 0] = 0.001

        return Pxx_copy

    def __binarize_slice(self, treshold, start=0, end=None):
        spectrogram_slice = self.__get_slice(start, end)
        return np.where(spectrogram_slice > treshold, 1, 0)

    def delete_area(
        self,
        area_treshold,
        start=0,
        end=None,
        delete_all=False,
        get_copy=False
    ):
        if delete_all:
            end = len(self.times)

        spectrogram_slice = self.__get_slice(start, end)

        if get_copy:
            spectrogram_slice = spectrogram_slice.copy()

        objects = self.get_object_coords(start, end)

        for object in objects:
            height, width = spectrogram_slice[object].shape

            if height < area_treshold:
                spectrogram_slice[object] = 0.001

        if get_copy:
            return spectrogram_slice

    def count_meteors(self, area_treshold, start=0, end=None):
        bin_spectrogram_slice = self.__binarize_slice(
            3.5 * self.default_treshold, start, end
        )
        spectrogram_slice = self.__get_slice(start, end)

        labeled_spectrogram, num_labels = ndimage.label(bin_spectrogram_slice)
        objects = ndimage.find_objects(labeled_spectrogram)

        for object in objects:
            height, width = bin_spectrogram_slice[object].shape

            if width > area_treshold and height > 27:
                spectrogram_slice[object] = 1000000

    def __create_blocks(self, height=3, width=10, fmin=600, fmax=1400):
        print(f'\nDividing spectrogram into {height * width} blocks...')
        Pxx_copy = np.copy(self.Pxx_modified[
            (self.frequencies >= fmin) & (self.frequencies <= fmax)
        ])
        h, w = Pxx_copy.shape

        print(
            f'Resizing array with width of {w} columns and height of {h} rows'
            f' into an array with a number of columns that can\nbe divided by'
            f' {width} and a number of rows that can be divided by {height}...'
        )
        height_surplus = h % height
        width_surplus = w % width

        if height_surplus:
            Pxx_copy = Pxx_copy[:-height_surplus]
        if width_surplus:
            Pxx_copy = Pxx_copy[:, :-width_surplus]

        h, w = Pxx_copy.shape
        print(f'New array has width of {w} columns and height of {h} rows.')

        row_per_block = h // height
        col_per_block = w // width
        print(
            f'Returned array will contain {height * width} blocks.\n'
            f'Each block will have a width of {col_per_block} columns'
            f' and a height of {row_per_block} rows.'
        )

        return (
            Pxx_copy
            .reshape(h // row_per_block, row_per_block, -1, col_per_block)
            .swapaxes(1, 2)
            .reshape((height * width), row_per_block, col_per_block)
        )

    def find_noise_mean(self):
        pxx_blocks = self.__create_blocks()
        print(f'Block array shape : {pxx_blocks.shape}')
        print('\nFinding best filter treshold...')
        block_info = []

        print('Saving variance, mean and index of previous created blocks...')
        for index, block in enumerate(pxx_blocks):
            block_info.append({
                'variance': np.var(block),
                'percentile_95': np.percentile(block, 95),
                'index': index,
            })

        all_var_median = np.median([block['variance'] for block in block_info])
        print(
            'Removing all blocks with a variance higher than '
            f'{all_var_median}...'
        )
        block_info = [
            block for block in block_info if block['variance'] < all_var_median
        ]

        max_percentile = np.max(
            [block['percentile_95'] for block in block_info]
        )
        print(
            'Taking block with 95th percentile value equal to '
            f'{max_percentile}...'
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
        print(f'Original percentile is {block_info[0]["percentile_95"]}.')
        print(f'Percentile after convolution is {percentile}.')
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
        if filter_all:
            spectrogram_slice = self.Pxx_modified
        else:
            spectrogram_slice = self.__get_slice(start, end)

        print('\nFiltering each column...')
        print(
            'During this procedure, the system will first calculate the '
            f'{percentile}th percentile of the column.\n'
            'All the values of the column below that percentile will be set '
            'to 0.001.'
        )

        for column in spectrogram_slice.T:
            column_percentile = np.percentile(column, percentile)
            column[column < column_percentile] = 0.001

    def keep_meteors_only(self, start=0, end=None, filter_all=False):
        column_info = []

        if filter_all:
            end = len(self.times)

        bin_spectrogram = self.__binarize_slice(10, start, end)

        for index, column in enumerate(bin_spectrogram.T):
            print(index)
            labeled_spectrogram, num_labels = ndimage.label(column)
            objects = ndimage.find_objects(labeled_spectrogram)
            for object in objects:
                print(object)
            column_info.append({
                'column_index': index,
                'objects': num_labels,
            })

    def get_potential_meteors(self, start=0, end=None, get_all=False):
        if get_all:
            end = len(self.times)

        spectrogram_copy = self.__get_slice(start, end, get_copy=True)

        for i in range(len(spectrogram_copy.T)):
            self.delete_area(27, start=i)

        object_coords = self.get_object_coords(get_all=True)
        print(object_coords[0][0].start)

    def get_object_coords(self, start=0, end=None, get_all=False, treshold=1):
        if get_all:
            end = len(self.times)

        bin_spectrogram_slice = self.__binarize_slice(
            treshold, start, end
        )

        labeled_spectrogram, num_labels = ndimage.label(bin_spectrogram_slice)
        return ndimage.find_objects(labeled_spectrogram)

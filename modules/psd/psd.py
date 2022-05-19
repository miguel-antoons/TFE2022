#! /usr/bin/env python3
'''
noise_psd.py

usage:
    noise_psd.py <data_path>/RAD_BEDOUR_20211124_1400_BEOUDS_SYS001.wav  -v




written by Michel Anciaux, 25-Mar-2022
updated by Miguel Antoons, Apr-2022

'''
import numpy as np

from scipy import signal


def get_psd(f, flow=800, fhigh=900):
    freq, S, fbin = f.FFT(f.Isamples)
    idx = (freq >= flow) * (freq < fhigh)
    p = (S[idx] * S[idx].conj()).real / 2

    psd = p.mean() / fbin

    return psd


def get_noise_psd(f):
    return get_psd(f, 800, 900)


def get_calibrator_psd(f):
    calibrator_frequency = get_calibrator_f(f)

    if calibrator_frequency:
        psd = (
            get_psd(f, calibrator_frequency - 5, calibrator_frequency + 5)
            - get_psd(f, calibrator_frequency - 15, calibrator_frequency - 5)
        )
        return (
            psd,
            calibrator_frequency
        )

    return None, None


def get_calibrator_f(
    f,
    fmin=1350,
    fmax=1750
):
    freq, S, fbin = f.FFT(f.Isamples)
    idx = (freq >= fmin) * (freq < fmax)

    max_index = np.abs(S[idx]).argmax()

    return freq[idx][max_index]


def get_calibrator_f_old(
    f,
    fmin=1350,
    fmax=1650
):
    frequencies, times, Pxx = signal.spectrogram(
            f.Isamples,
            f.fs,
            nperseg=16384,
            noverlap=14384,
            window='hann',
        )
    frequency_resolution = f.fs / 2 / len(frequencies)

    same_index = 0
    previous_index = 0
    index = 0
    min_row = round(fmin / frequency_resolution)
    max_row = round(fmax / frequency_resolution)

    # print(f'Searching direct signal between {fmin} Hz and {fmax} Hz...')

    while not same_index == 50 and index < len(times):
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
        # print(
        #     'Calibrator signal was not found, therefore psd cannot be '
        #     'calculated.'
        # )
        return False

    # print(
    #     'Direct signal was found around '
    #     f'{(previous_index + min_row) * frequency_resolution} Hz.'
    # )
    return (previous_index + min_row) * frequency_resolution

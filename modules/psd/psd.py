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
    """
    Function calculates the psd of a wav file between 2 frequencies

    Parameters
    ----------
    f : BramsWavFile
        instance of the wav file
    flow : int, optional
        lower frequency from which to calculate the psd, by default 800
    fhigh : int, optional
        upper frequency upto which to calculate psd, by default 900

    Returns
    -------
    float
        the calculated psd
    """
    # get fourier transform from BramsWavFile class
    freq, S, fbin = f.FFT(f.Isamples)
    idx = (freq >= flow) * (freq < fhigh)

    # calculate the total power of the wanted frequencies
    # divided by 2 to prevent having the negative frequencies added to the
    # positives
    p = (S[idx] * S[idx].conj()).real / 2

    # get a mean normalized to 1Hz
    psd = p.mean() / fbin

    return psd


def get_noise_psd(f):
    """
    Function calculates the psd value of the noise in a BRAMS wav file

    Parameters
    ----------
    f : BramsWavFile
        wav file to calculate noise from

    Returns
    -------
    float
        noise psd of a BRAMS wav file
    """
    return get_psd(f, 800, 900)


def get_calibrator_psd(f):
    """
    Function calculates the psd of the calibrator signal

    Parameters
    ----------
    f : BramsWavFile
        waf file to calculate the calibrator signal psd of

    Returns
    -------
    float or None
        None if the calibrator frequency was not found, or the calibrator psd
    """
    calibrator_frequency = get_calibrator_f(f)

    if calibrator_frequency:
        # calculate the psd and subtract noise psd from it
        # this is done in order to get a more accurate measure
        psd = (
            get_psd(f, calibrator_frequency - 9, calibrator_frequency + 9)
            - get_psd(f, calibrator_frequency - 27, calibrator_frequency - 9)
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
    """
    Function tries to retrieve the calibrator's frequency of a BramsWavFile
    between 2 frequencies

    Parameters
    ----------
    f : BramsWavFile
        file to retrieve the calibrator frequency from
    fmin : int, optional
        lower frequency from which to search the calibrator frequency
        , by default 1350
    fmax : int, optional
        upper frequency upto which search the calibrator frequency
        , by default 1750

    Returns
    -------
    float
        found frequency of the calibrator signal
    """
    # calculate fft of the wav signal
    freq, S, fbin = f.FFT(f.Isamples)
    idx = (freq >= fmin) * (freq < fmax)

    # retrieve the highest value of the fft
    max_index = np.abs(S[idx]).argmax()

    return freq[idx][max_index]


def get_calibrator_f_old(
    f,
    fmin=1350,
    fmax=1650
):
    # * currently not used
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

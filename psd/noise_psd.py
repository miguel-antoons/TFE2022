#! /usr/bin/env python3
'''
noise_psd.py

usage:
    noise_psd.py <data_path>/RAD_BEDOUR_20211124_1400_BEOUDS_SYS001.wav  -v




written by Michel Anciaux, 25-Mar-2022

'''
from brams.brams_wav_2 import BramsWavFile
import argparse


def SSB_noise(f, flow=800, fhigh=900, skip_seconds=0.1, verbosity=1):
    # f = brams_wav.BramsWavFile(filename)
    freq, S, fbin = f.FFT(f.Isamples)
    idx = (freq >= flow) * (freq < fhigh)
    p = (S[idx] * S[idx].conj()).real / 2
    # psd = power / idx.sum() / fbin
    psd = p.mean() / fbin
    # if verbosity > 0:
    #     print(
    #         "\tSSB noise in [{:.0f}, {:.0f}] Hz".format(
    #             flow, fhigh))
    #     print(
    #         "\t\tpower: {:.2g} [ADU²] psd: {:.3g} [ADU²/Hz]".format(
    #             power, psd))
    return psd


def GetArguments():
    parser = argparse.ArgumentParser(
        description='determine SSB noise from BRAMS WAV file')
    parser.add_argument(
        "filename", help="name of WAV file")
    parser.add_argument(
        "-v", "--verbosity",
        help="print more information", action="count", default=0)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = GetArguments()

    if args.verbosity > 0:
        print(args)

    f = BramsWavFile(args.filename, args.verbosity)

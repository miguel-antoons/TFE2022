#! /usr/bin/env python3
'''
brams_wav
=========

Provides a class to access data from a WAV file with the BRAMS subchunks.
Normal WAV files without these subchunks can also be read.

usage:

    f = BramsWavFile(args.filename)

written by Michel Anciaux 10-Mar-2015
modified by Miguel Antoons april-2022
'''
import numpy as np
import tarfile

from scipy.signal import windows
from scipy.fft import rfft, rfftfreq


class BramsError(Exception):
    def __init__(self, filename, msg=None):
        if msg is None:
            msg = "generic Brams error with {}".format(filename)
        super(BramsError, self).__init__(msg)
        self.filename = filename


class BramsWavFile:
    head_t = np.dtype([
        ('ID', '<S4'),
        ('size', '<u4')])

    riff_t = np.dtype([
        ('head', head_t),
        ('format', '<S4')])

    fmt_t = np.dtype([
        ('audio_format', '<u2'),
        ('num_channels', '<u2'),
        ('sample_rate', '<u4'),
        ('byte_rate', '<u4'),
        # number of bytes per sample
        # (num_channels * bits_per_sample / 8 bits/byte)
        ('block_align', '<u2'),
        ('bits_per_sample', '<u2')])

    bra1_t = np.dtype([
        ('version', '<u2'),
        ('sample_rate', '<f8'),
        ('LO_freq', '<f8'),
        ('start', '<u8'),
        ('PPS_count', '<u8'),
        ('beacon_latitude', '<f8'),
        ('beacon_longitude', '<f8'),
        ('beacon_altitude', '<f8'),
        ('beacon_frequency', '<f8'),
        ('beacon_power', '<f8'),
        ('beacon_polarisation', '<u2'),
        ('antenna_ID', '<u2'),
        ('antenna_latitude', '<f8'),
        ('antenna_longitude', '<f8'),
        ('antenna_altitude', '<f8'),
        ('antenna_azimuth', '<f8'),
        ('antenna_elevation', '<f8'),
        ('beacon_code', '<S6'),
        ('observer_code', '<S6'),
        ('station_code', '<S6'),
        ('description', '<S234'),
        ('reserved', '<S256')])

    def getNextSubChunk(self, file, offset=0):
        head = np.fromfile(
            file,
            dtype=self.head_t,
            count=1,
            offset=offset
        )[0]

        # read the chunk following the header
        subchunk_offset = offset + self.head_t.itemsize
        return head['ID'], head['size'], subchunk_offset

    def getRiffChunk(self, file):
        # get first available chunk from the .wav file
        # (aka RIFF chunk descriptor)
        riff = np.fromfile(
            file, dtype=self.riff_t, count=1)[0]
        if (riff['head']['ID'] != b"RIFF") or (riff['format'] != b"WAVE"):
            raise BramsError(file.name)

        # return the total size following the RIFF chunk
        return (
            riff['head']['size'] - self.riff_t.itemsize + self.head_t.itemsize
        )

    def __init__(self, filename, tar_member=None):
        if tar_member is None:
            file = filename
        else:
            with tarfile.open(filename) as tar:
                file = tar.extractfile(tar_member)

        n_to_read = self.getRiffChunk(file)

        self.fs = None
        self.fft_freq = None
        self.fft_fbin = None
        self.fft = None
        data_offset = self.riff_t.itemsize

        while n_to_read >= self.head_t.itemsize:
            try:
                hid, hsize, subchunk_offset = self.getNextSubChunk(
                    file,
                    data_offset
                )
            except EOFError:
                raise BramsError("Unexpected EOF")
            data_offset = hsize + subchunk_offset
            n_to_read -= hsize + self.head_t.itemsize

            if hid == b'fmt ':
                fmt = np.fromfile(
                    file,
                    dtype=self.fmt_t,
                    count=1,
                    offset=subchunk_offset
                )[0]

            elif hid == b'BRA1':
                bra1 = np.fromfile(
                    file,
                    dtype=self.bra1_t,
                    count=1,
                    offset=subchunk_offset
                )[0]
                self.fs = bra1['sample_rate']
            elif hid == b'data':
                data = np.fromfile(
                    file,
                    dtype='<i2',
                    count=int(hsize/2),
                    offset=subchunk_offset
                )

                self.Isamples = data[:]

                if self.fs is not None:
                    break

        if self.fs is None:
            # print(self.fmt)
            self.fs = fmt['sample_rate']

    def skip_samples(self, start_second=0.1):

        start_index = int(start_second * self.fs)
        stop_index = len(self.Isamples)

        Isamples = self.Isamples[start_index:stop_index]

        return Isamples

    def FFT(self, Isamples, force_new=False):
        if (
            self.fft is not None
            and self.fft_fbin is not None
            and self.fft_freq is not None
            and not force_new
        ):
            return self.fft_freq, self.fft, self.fft_fbin
        nsamples = Isamples.size
        w = windows.hann(nsamples)
        w_scale = 1 / w.mean()
        Isamples = Isamples * w * w_scale

        S = rfft(Isamples) / nsamples
        S[1: -1] *= 2

        self.fft = S
        self.fft_fbin = self.fs / nsamples
        self.fft_freq = rfftfreq(nsamples, 1 / self.fs)

        return self.fft_freq, S, self.fft_fbin

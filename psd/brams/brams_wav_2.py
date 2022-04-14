#! /usr/bin/env python3
'''
brams_wav
=========

Provides a class to access data from a WAV file with the BRAMS subchunks.
Normal WAV files without these subchunks can also be read.

usage:

    f = BramsWavFile(args.filename)

written by Michel Anciaux 10-Mar-2015
'''
import numpy as np
from scipy.signal import windows
from scipy.io import wavfile


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

    def getNextSubChunk(self, f):
        # cur_pos = f.tell()
        # read next chunk header
        hstring = f.read(self.head_t.itemsize)
        if len(hstring) == 0:
            raise EOFError

        # convert the header to readable data
        head = np.frombuffer(hstring, dtype=self.head_t, count=1)[0]

        # read the chunk following the header
        subchunk = f.read(head['size'])
        return head['ID'], head['size'], subchunk

    def getRiffChunk(self, f):
        # get first available chunk from the .wav file
        # (aka RIFF chunk descriptor)
        riff = np.frombuffer(
            f.read(self.riff_t.itemsize), dtype=self.riff_t, count=1)[0]
        if (riff['head']['ID'] != b"RIFF") or (riff['format'] != b"WAVE"):
            raise BramsError(f.name)

        # return the total size following the RIFF chunk
        return (
            riff['head']['size'] - self.riff_t.itemsize + self.head_t.itemsize
        )

    def __init__(self, filename):
        f = open(filename, 'rb')
        n_to_read = self.getRiffChunk(f)

        self.fs = None
        while n_to_read >= self.head_t.itemsize:
            try:
                hid, hsize, subchunk = self.getNextSubChunk(f)
            except EOFError:
                raise BramsError("Unexpected EOF")
            n_to_read -= hsize + self.head_t.itemsize
            # print(hid, hsize)
            if hid == b'fmt ':
                fmt = np.frombuffer(subchunk, dtype=self.fmt_t, count=1)[0]

            elif hid == b'BRA1':
                bra1 = np.frombuffer(
                    subchunk, dtype=self.bra1_t, count=1)[0]
                self.fs = bra1['sample_rate']
            elif hid == b'data':
                self.nsamples = hsize // fmt['block_align']
                data = np.frombuffer(subchunk, dtype='<i2', count=-1)

                self.Isamples = data[:]

                if self.fs is not None:
                    break

        f.close()

        if self.fs is None:
            # print(self.fmt)
            self.fs = fmt['sample_rate']

    def skip_samples(self, start_second=0.1):

        start_index = int(start_second * self.fs)
        stop_index = self.nsamples

        Isamples = self.Isamples[start_index:stop_index]

        return Isamples

    def FFT(self, Isamples):
        nsamples = Isamples.size
        w = windows.hann(Isamples.size)
        w_scale = 1 / w.mean()
        Isamples = Isamples * w * w_scale

        S = np.fft.rfft(Isamples) / nsamples
        S[1: -1] *= 2

        return np.fft.rfftfreq(nsamples, 1 / self.fs), S, self.fs / nsamples

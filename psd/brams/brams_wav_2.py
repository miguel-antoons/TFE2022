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
import os


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

    def putRiffChunk(self, f, size_bytes):
        riff = np.zeros(1, self.riff_t)
        r = riff[0]
        r['head']['ID'] = b'RIFF'
        r['head']['size'] = size_bytes - self.head_t.itemsize
        r['format'] = b'WAVE'
        return f.write(r)

    def putFmtChunk(self, f):
        head = np.array((b'fmt ', self.fmt_t.itemsize), self.head_t)
        nwritten = f.write(head)
        nwritten += f.write(self.fmt)
        return nwritten

    def putBra1Chunk(self, f):
        head = np.array((b'BRA1', self.bra1_t.itemsize), self.head_t)
        nwritten = f.write(head)
        nwritten += f.write(self.bra1)
        return nwritten

    def putDataChunk(self, f):
        data = np.empty(self.Isamples.size * self.nchannels, dtype='<i2')

        if self.nchannels == 2:
            data[0::2] = self.Isamples
            data[1::2] = self.Qsamples
        else:
            data = self.Isamples
        head = np.array((b'data', data.itemsize * data.size), self.head_t)
        nwritten = f.write(head)
        nwritten += f.write(data)
        return nwritten

    def putBra2Chunk(self, f):
        periods = np.empty(self.nperiods * 2, dtype='<u8')
        periods[0::2] = self.time_index
        periods[1::2] = self.time * 1000000
        head = np.array(
            (b'BRA2', periods.itemsize * periods.size), self.head_t)
        nwritten = f.write(head)
        nwritten += f.write(periods)
        return nwritten

    def __init__(self, filename, verbosity=0):

        self.filename = os.path.basename(filename)
        # import ipdb; ipdb.set_trace()
        f = open(filename, 'rb')
        n_to_read = self.getRiffChunk(f)
        # total size of the .wav file
        self.size = n_to_read + self.riff_t.itemsize

        # print(self.size, n_to_read)
        self.bra1 = None
        self.bra2 = None
        while n_to_read >= self.head_t.itemsize:
            try:
                hid, hsize, subchunk = self.getNextSubChunk(f)
            except EOFError:
                raise BramsError("Unexpected EOF")
            n_to_read -= hsize + self.head_t.itemsize
            # print(hid, hsize)
            if hid == b'fmt ':
                fmt = np.frombuffer(subchunk, dtype=self.fmt_t, count=1)[0]
                self.fmt = fmt
                self.nchannels = fmt['num_channels']
                if self.nchannels > 2:
                    raise BramsError(
                        "Unable to handle {} channels".format(self.nchannels))
            elif hid == b'BRA1':
                self.bra1 = np.frombuffer(
                    subchunk, dtype=self.bra1_t, count=1)[0]
                self.fs = self.bra1['sample_rate']
                self.LO_freq = self.bra1['LO_freq']
            elif hid == b'data':
                self.nsamples = hsize // fmt['block_align']
                data = np.frombuffer(subchunk, dtype='<i2', count=-1)

                if self.nchannels == 2:
                    # get every even index starting from 0
                    self.Isamples = data[0::2]
                    # get every even index STARTING FROM 1
                    self.Qsamples = data[1::2]
                else:
                    self.Isamples = data[:]
                    self.Qsamples = None
            elif hid == b'BRA2':
                periods = np.frombuffer(subchunk, dtype='<u8', count=-1)
                self.time = periods[1::2] / 1e6
                self.time_index = periods[0::2]
                self.nperiods = len(self.time)
                self.period_frames = self.nsamples // self.nperiods
            elif hid == b'inf1':
                pass
                # raise BramsError("handling of inf1 subchunk not implemented")
            else:
                # raise BramsError("unknown subchunk")
                if verbosity > 0:
                    print("\n\tunknown subchunk\n")
        f.close()
        if self.bra1 is None:
            if verbosity > 0:
                print("\n\tNOT a BRAMS wave file!!\n")
                if verbosity > 1:
                    for name in self.fmt_t.names:
                        print("\t{}: {}".format(name, self.fmt[name]))
            # print(self.fmt)
            self.fs = self.fmt['sample_rate']
            if self.bra2 is None:
                self.period_frames = None
                self.nperiods = None
        else:
            self.beacon_code = self.bra1['beacon_code']
            self.station_code = self.bra1['station_code']

    def __del__(self):
        ...

    def skip_samples(self, start_second=0.1, stop_second=None):

        start_index = int(start_second * self.fs)
        if start_index >= self.nsamples:
            raise ValueError("start_second too high")

        if stop_second is None:
            stop_index = self.nsamples
        else:
            stop_index = int(stop_second * self.fs)
        if stop_index > self.nsamples:
            stop_index = self.nsamples

        Isamples = self.Isamples[start_index:stop_index]
        if self.nchannels == 2:
            Qsamples = self.Qsamples[start_index:stop_index]
        else:
            Qsamples = None
        return (Isamples, Qsamples)

    def print_stats(self, Isamples=None, Qsamples=None):
        if Isamples is None:
            Isamples = self.Isamples
        if Qsamples is None:
            Qsamples = self.Qsamples
        print(
            "\t{} channel{:1s}, ".format(
                self.nchannels, "" if self.nchannels == 1 else "s"),
            "{} samples, ".format(Isamples.size),
            "{} frames per period, ".format(self.period_frames),
            "{} periods".format(self.nperiods))
        print(
            "\tIsamples max: ", Isamples.max(), "min: ", Isamples.min(),
            "std: {:.2f}".format(Isamples.std()),
            "signal power: {:.2g} [ADU²]".format(
                (Isamples.astype(float)**2).mean()))

    def FFT(self, Isamples=None, Qsamples=None, both_sidebands=False):
        if Isamples is None:
            Isamples = self.Isamples
        if Qsamples is None and self.Qsamples:
            Qsamples = self.Qsamples

        nsamples = Isamples.size
        w = windows.hann(Isamples.size)
        w_scale = 1 / w.mean()
        Isamples = Isamples * w * w_scale
        if self.Qsamples:
            Qsamples = Qsamples * w * w_scale

        # x axis of the fourier tranform
        self.freq = np.fft.rfftfreq(nsamples, 1 / self.fs)

        if self.nchannels == 2 and (self.bra1 or both_sidebands):
            if both_sidebands:
                self.Su = np.fft.rfft(Isamples) / nsamples
                self.Su[1: -1] *= 2
                self.Sl = np.fft.rfft(Qsamples) / nsamples
                self.Sl[1: -2] *= 2
                return self.freq, [self.Su, self.Sl]
            else:
                S = np.fft.fft(Isamples + 1j * Qsamples) / nsamples
                S[1: -1] *= 2
        else:
            S = np.fft.rfft(Isamples) / nsamples
            S[1: -1] *= 2
        self.S = S
        self.fbin = self.fs / nsamples

        return self.freq, self.S, self.fbin

    def print_spectral_stats(
            self, freq, S, fnoise_lower=None, fnoise_upper=None):
        if fnoise_lower is None:
            fnoise_lower = freq[0]
        if fnoise_upper is None:
            fnoise_upper = freq[-1]
        fbin = freq[1] - freq[0]
        S_power = (S * S.conj()).real / 2
        noise_psd = (
            S_power[
                    (freq > fnoise_lower)
                & (freq < fnoise_upper)].mean() / fbin)
        print(
            "\tspectral power: {:.2g} [ADU²] ".format(S_power.sum())
            + "PSD: {:.2g} [ADU²/Hz] ".format(noise_psd)
            + "({} -- {} Hz)".format(fnoise_lower, fnoise_upper))

    def save_as(self, filename=None):
        if filename is None:
            filename = self.filename
        self.filename = os.path.basename(filename)
        # import ipdb; ipdb.set_trace()
        f = open(filename, 'wb')
        f.seek(self.riff_t.itemsize)
        size = self.riff_t.itemsize
        size += self.putFmtChunk(f)
        size += self.putBra1Chunk(f)
        size += self.putDataChunk(f)
        size += self.putBra2Chunk(f)
        f.seek(0)
        self.putRiffChunk(f, size)
        f.close()

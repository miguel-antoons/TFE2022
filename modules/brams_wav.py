#! /usr/bin/env python3
'''
brams_wav
=========

Provides a class to access data from a WAV file with the BRAMS subchunks.

written by Michel Anciaux 10-Mar-2015
modified by Miguel Antoons april-2022
'''
import os
import numpy as np
import tarfile

from scipy.signal import windows
from scipy.fft import rfft, rfftfreq
from datetime import datetime, timedelta, timezone


class BramsError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "An unknown error occured."
        super(BramsError, self).__init__(msg)


class DirectoryNotFoundError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = 'The requested directory does not exist.'
        super(DirectoryNotFoundError, self).__init__(msg)


class BramsWavFile:
    """
    Function decodes searches and stores a BRAMS wav file.
    It can also calculate the fft of a Brams wav file.
    """
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
        ('bits_per_sample', '<u4')])

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
        """
        Function gets the subchunk coming after the given offset

        Parameters
        ----------
        file : bytes
            the file to get the subchunk from
        offset : int, optional
            the offset after which to take the subchunk, by default 0

        Returns
        -------
        tuple
            id, size and offset to data. It gets these values from the
            subchunk header
        """
        head = np.frombuffer(
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
        riff = np.frombuffer(
            file, dtype=self.riff_t, count=1)[0]
        if (riff['head']['ID'] != b"RIFF") or (riff['format'] != b"WAVE"):
            raise BramsError(file.name)

        # return the total size following the RIFF chunk
        return (
            riff['head']['size'] - self.riff_t.itemsize + self.head_t.itemsize
        )

    def __get_wav(
        self,
        directory: str,
        filename: str,
        station: str,
        date_time: datetime,
        alias: str = 'SYS001',
        respect_date: bool = False,
    ):
        """
        Function verifies if the given file name is from the requested wav
        file. If this is the case, it returns the file contents in bytes.

        Parameters
        ----------
        directory : str
            directory in which the file is located
        filename : str
            name of the file
        station : str
            station from which the file should be
        date_time : datetime
            date the searches file should be produced
        alias : str, optional
            antenna number of the requested file, by default 'SYS001'
        respect_date : bool, optional
            wether to respect the date precisely or not, by default False

        Returns
        -------
        bytes
            the wav file content if it is the requested file
        """
        # if the filename is from a non wav file
        if filename.find('.wav') == -1:
            return False

        split_filename = filename.split('_')

        # check the date of the filename
        file_datetime = datetime.strptime(
            f'{split_filename[2]}{split_filename[3]}',
            '%Y%m%d%H%M'
        ).replace(tzinfo=timezone.utc)

        file_alias = split_filename[5].replace('.wav', '')

        # set datetime boundaries
        if respect_date:
            min_date = date_time - timedelta(minutes=3)
            max_date = date_time + timedelta(minutes=3)
        else:
            min_date = date_time - timedelta(minutes=20)
            max_date = date_time + timedelta(minutes=20)

        # if the file is not the requested file
        if not (
            file_datetime <= max_date
            and file_datetime >= min_date
            and split_filename[4] == station
            and file_alias == alias
        ):
            return False

        self.date = file_datetime
        self.filename = filename
        # if the file is the requested file, return its contents
        with open(os.path.join(directory, filename), 'rb') as wav_file:
            return wav_file.read()

    def __get_wav_from_tar(
        self,
        directory: str,
        filename: str,
        station: str,
        date_time: datetime,
        alias: str = 'SYS001',
        respect_date: bool = False,
    ):
        """
        Function verifies if a requested file is located in the given filename.
        If this is the case, it extracts the requested file from the tar file.

        Parameters
        ----------
        directory : str
            directory in which the file is located
        filename : str
            name of the file
        station : str
            station from which the file should be
        date_time : datetime
            date the searches file should be produced
        alias : str, optional
            antenna number of the requested file, by default 'SYS001'
        respect_date : bool, optional
            wether to respect the date precisely or not, by default False

        Returns
        -------
        bytes the contents of the wav file that was in the tar archive
            _description_
        """
        # if the filename is from a non tar file
        if filename.find('.tar') == -1:
            return False

        split_filename = filename.split('_')

        # check if the filename contains the requested date
        file_datetime = datetime.strptime(
            f'{split_filename[2]}{split_filename[3]}',
            '%Y%m%d%H%M'
        ).replace(tzinfo=timezone.utc)
        file_datetime_1h = file_datetime + timedelta(hours=1)

        file_alias = split_filename[5].replace('.tar', '')

        # if the filename is not from the requested file
        if not (
            file_datetime <= date_time
            and file_datetime_1h > date_time
            and split_filename[4] == station
            and file_alias == alias
        ):
            return False

        if respect_date:
            min_date = date_time - timedelta(minutes=3)
            max_date = date_time + timedelta(minutes=3)
        else:
            min_date = date_time - timedelta(minutes=20)
            max_date = date_time + timedelta(minutes=20)

        # if it is the requested file, extract it from the tar archive and
        # return its content in bytes
        with tarfile.open(os.path.join(directory, filename)) as tar_file:
            for member in tar_file.getmembers():
                split_filename = member.name.split('_')

                file_datetime = datetime.strptime(
                    f'{split_filename[2]}{split_filename[3]}',
                    '%Y%m%d%H%M'
                ).replace(tzinfo=timezone.utc)

                if (
                    file_datetime >= min_date
                    and file_datetime <= max_date
                    and not member.name.find('.wav') == -1
                ):
                    self.filename = member.name
                    self.date = file_datetime

                    return tar_file.extractfile(member).read()

        return False

    def __get_file(
        self,
        date_time: datetime,
        station: str,
        alias: str = 'SYS001',
        respect_date: bool = False,
        is_wav: bool = False,
        parent_directory: str = '/bira-iasb/data/GROUNDBASED/BRAMS/wav/',
        from_archive: bool = True,
    ):
        """
        Function tries to retrieve a BRAMS wav file inside the BRAMS archive
        or another directory

        Parameters
        ----------
        date_time : datetime
            datetime of the requested file
        station : str
            station that created the requested file
        alias : str, optional
            antenna that created the requested file, by default 'SYS001'
        respect_date : bool, optional
            wether to respect the requested date precisely or not
            , by default False
        is_wav : bool, optional
            wether the file is contained in a tar archive (False) or not (True)
            , by default False
        parent_directory : str, optional
            parent directory of the requested file
            , by default '/bira-iasb/data/GROUNDBASED/BRAMS/wav/'
        from_archive : bool, optional
            indicates if the requested file is located in the archive or not
            , by default True

        Returns
        -------
        bytes
            the content in bytes from the requested file

        Raises
        ------
        DirectoryNotFoundError
            raises this error if the directory was not found
        FileNotFoundError
            raised if the file is not found by the function
        """
        if from_archive:
            directory = (
                f"{parent_directory}{station}"
                f"/{date_time.strftime('%Y')}"
                f"/{date_time.strftime('%m')}"
                f"/{date_time.strftime('%d')}/"
            )
        else:
            directory = parent_directory

        # try to list the directory content
        try:
            dir_content = os.listdir(directory)
        except FileNotFoundError:
            raise DirectoryNotFoundError()

        # for each filename verify if it is the requested file
        for filename in dir_content:
            if is_wav:
                try:
                    file = self.__get_wav(
                        directory,
                        filename,
                        station,
                        date_time,
                        alias,
                        respect_date
                    )
                except FileNotFoundError:
                    continue
            else:
                try:
                    file = self.__get_wav_from_tar(
                        directory,
                        filename,
                        station,
                        date_time,
                        alias,
                        respect_date
                    )
                except FileNotFoundError:
                    continue

            if file and file is not None:
                return file

        raise FileNotFoundError()

    def __init__(
        self,
        date_time: datetime,
        station: str,
        alias: str = 'SYS001',
        respect_date: bool = False,
        is_wav: bool = False,
        parent_directory: str = '/bira-iasb/data/GROUNDBASED/BRAMS/wav/',
        from_archive: bool = True,
    ):
        """
        Function initializes the BramsWavFile class by tying to retrieve the
        requested file and separating its subchunks, thus containing all its
        information.

        Parameters
        ----------
        date_time : datetime
            date and time of the requested file
        station : str
            location code of the requested station
        alias : str, optional
            antenna number of the requested file, by default 'SYS001'
        respect_date : bool, optional
            wether to precisely respect the requested date or not
            , by default False
        is_wav : bool, optional
            wether the requested file is contained in a tar archive (False) or
            is a standalone wav file (True), by default False
        parent_directory : str, optional
            parent directory of the requested file
            , by default '/bira-iasb/data/GROUNDBASED/BRAMS/wav/'
        from_archive : bool, optional
            wether the file is located in the BRAMS archive or not
            , by default True

        Raises
        ------
        BramsError
            if the file is not found
        BramsError
            if there is an unexpected EOF
        """
        # retrieve the requested file
        try:
            file = self.__get_file(
                date_time,
                station,
                alias,
                respect_date,
                is_wav,
                parent_directory,
                from_archive
            )
        except FileNotFoundError:
            raise BramsError()

        n_to_read = self.getRiffChunk(file)

        self.fs = None
        self.fft_freq = None
        self.fft_fbin = None
        self.fft = None
        data_offset = self.riff_t.itemsize

        # read all the subchunks of the wav file
        while n_to_read >= self.head_t.itemsize:
            # get the next sub chunk in the wav file
            try:
                hid, hsize, subchunk_offset = self.getNextSubChunk(
                    file,
                    data_offset
                )
            except EOFError:
                raise BramsError("Unexpected EOF")

            # calculate the current offset in the file and the remaining bytes
            # to read from the wav file
            data_offset = hsize + subchunk_offset
            n_to_read -= hsize + self.head_t.itemsize

            # store each subchunk accordingly
            if hid == b'fmt ':
                fmt = np.frombuffer(
                    file,
                    dtype=self.fmt_t,
                    count=1,
                    offset=subchunk_offset
                )[0]

            elif hid == b'BRA1':
                bra1 = np.frombuffer(
                    file,
                    dtype=self.bra1_t,
                    count=1,
                    offset=subchunk_offset
                )[0]
                self.fs = bra1['sample_rate']
            elif hid == b'data':
                if hsize > (len(file) - subchunk_offset):
                    hsize = len(file) - subchunk_offset

                data = np.frombuffer(
                    file,
                    dtype='<i2',
                    count=int(hsize/2),
                    offset=subchunk_offset
                )

                self.Isamples = data[:]

                if self.fs is None:
                    self.fs = fmt['sample_rate']

                # after this subchunk, the rest is not necessary, so break the
                # loop
                break

    def FFT(self, Isamples, force_new=False):
        """
        Calculates the fft of the wav file contained in this class

        Parameters
        ----------
        Isamples : np.array
            array containing the audio data of the wav file
        force_new : bool, optional
            wether to force a new fft calculation even if one already exists
            , by default False

        Returns
        -------
        tuple
            fft x axis, fft values and the fft bins
        """
        if (
            self.fft is not None
            and self.fft_fbin is not None
            and self.fft_freq is not None
            and not force_new
        ):
            return self.fft_freq, self.fft, self.fft_fbin

        # get the length of all the audio samples
        nsamples = Isamples.size

        # create a window function
        w = windows.hann(nsamples)
        w_scale = 1 / w.mean()

        # apply that window on all the audio samples
        Isamples = Isamples * w * w_scale

        # get the Fourier Tranform and normalize it
        S = rfft(Isamples) / nsamples
        S[1: -1] *= 2

        self.fft = S
        self.fft_fbin = self.fs / nsamples
        self.fft_freq = rfftfreq(nsamples, 1 / self.fs)

        return self.fft_freq, S, self.fft_fbin

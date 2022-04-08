import os
import time
from noise_psd import SSB_noise
from brams.brams_wav_2 import BramsWavFile


def main(directory=None, n_files=288, time_all=False):
    start_time = time.time()

    if directory is None:
        directory = os.path.join(os.getcwd(), 'psd\\recordings\\BEHAAC')
    directory_content = os.listdir(directory)

    if time_all:
        n_files = len(directory_content)

    for i in range(n_files):
        print(i)
        file_path = os.path.join(directory, directory_content[i])

        # check the path is a file
        if os.path.isfile(file_path):
            f = BramsWavFile(file_path)
            power, psd, rms = SSB_noise(f)

    return time.time() - start_time


if __name__ == '__main__':
    print(f'\n------program execution took {main()} seconds------')

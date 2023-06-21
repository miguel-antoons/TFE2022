import os
import time
from noise_psd import SSB_noise
from modules.brams_wav_2 import BramsWavFile


def main(directory='recordings/BEHAAC', n_files=288, time_all=False):
    start_time = time.time()

    directory = os.path.join(os.getcwd(), directory)
    directory_content = os.listdir(directory)

    if time_all:
        n_files = len(directory_content)

    for i in range(n_files):
        # print(i)
        file_path = os.path.join(directory, directory_content[i])

        # check the path is a file
        if os.path.isfile(file_path):
            f = BramsWavFile(file_path)
            psd = SSB_noise(f)
            print(psd)

    return time.time() - start_time


if __name__ == '__main__':
    print(f'\n------program execution took {main()} seconds------')

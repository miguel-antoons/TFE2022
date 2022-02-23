from scipy import signal
from scipy.fft import fftshift
import matplotlib.pyplot as plt
import wave


def main():
    print("Loading wav file into memory")
    recording_info = wave.open(
        './recordings/RAD_BEDOUR_20220211_1730_BEDINA_SYS001.wav',
        'r'
    )

    sound_signal = recording_info.readframes(500)
    print(recording_info.getparams())
    print(sound_signal)

    return


if __name__ == '__main__':
    main()

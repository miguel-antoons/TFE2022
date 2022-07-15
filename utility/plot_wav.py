import matplotlib.pyplot as plt
import numpy as np
import wave
import sys


def plot_wave(path):
    spf = wave.open(path, "r")

    # Extract Raw Audio from Wav File
    signal = spf.readframes(-1)
    signal = np.frombuffer(signal, dtype='<i2')
    x = [i / 5512.5 for i in range(0, len(signal))]

    if spf.getnchannels() == 2:
        print("Just mono files")
        sys.exit(0)

    generate_plot(
        x,
        signal,
        'tfe_plot',
        title='Humain 1 le 1er mai 2022 à 6h10',
        x_title='Temps (secondes)',
        y_title='Amplitude'
    )


def generate_plot(
    x,
    y,
    im_name,
    width=26.5,
    height=14.4,
    figure_n=0,
    dpi=350.0,
    title='',
    y_title='',
    x_title='',
    y_min=None,
    y_max=None,
):
    plt.rcParams['agg.path.chunksize'] = 10000
    plt.rcParams.update({'font.size': 22})
    plt.figure(num=figure_n, figsize=(width, height), dpi=dpi)
    plt.plot(x, y)

    axis = plt.gca()
    axis.set_ylim([y_min, y_max])
    plt.title(title)
    plt.xlabel(x_title)
    plt.ylabel(y_title)

    plt.savefig(f'{im_name}.png')
    plt.close(figure_n)
    print(im_name)


if __name__ == '__main__':
    plot_wave(
        '/home/niutalol/Documents/TFE2022/recordings/utility/'
        'RAD_BEDOUR_20220501_0610_BEHUMA_SYS001.wav'
    )

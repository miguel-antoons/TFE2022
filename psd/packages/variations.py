import matplotlib.pyplot as plt
import numpy as np

from scipy.optimize import curve_fit


def fit_func(x, a, b):
    x = np.array(x)
    return a * x + b


def detect_noise_decrease(x_data, y_data, start_index=0, interval=150):
    if start_index < interval:
        return

    x = x_data[start_index - interval:start_index]
    y = y_data[start_index - interval:start_index]

    popt, pcov = curve_fit(fit_func, x, y)

    if popt[0] < -15:
        print(popt)
        print(f'A significative decrease at index {start_index}')
        plt.plot(x, fit_func(x, *popt), 'r-')
        plt.plot(x, y)
        plt.show()


def detect_noise_increase(previous_value, current_value, current_index):
    if current_value > previous_value * 10:
        print(f'A signigicative noise increase at index {current_index}')

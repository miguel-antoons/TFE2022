# import matplotlib.pyplot as plt
import numpy as np

from scipy.optimize import curve_fit


def fit_func(x, a, b):
    x = np.array(x)
    return a * x + b


def detect_noise_decrease(x_data, y_data, index, interval=150):
    if len(x_data) < interval:
        return False

    if not len(x_data) == len(y_data):
        return False

    if len(x_data) > interval:
        x_data = x_data[-interval:]
        y_data = y_data[-interval:]

    popt, pcov = curve_fit(fit_func, x_data, y_data)

    if popt[0] < -15:
        # print(popt)
        # print(f'A significative decrease at index {index}')
        return True
        # plt.plot(x, fit_func(x, *popt), 'r-')
        # plt.plot(x, y)
        # plt.show()

    return False


def detect_noise_increase(previous_value, current_value, current_index):
    if current_value > previous_value * 10:
        # print(f'A significative noise increase at index {current_index}')
        return True

    return False


def detect_calibrator_variations(previous_value, current_value):
    if current_value is None:
        # print('No calibrator signal was detected!!')
        return 100
    elif previous_value is None:
        # print('No value to compare the current value to')
        return 0

    difference = (current_value / previous_value - 1) * 10

    # if abs(difference) > 50:
    #     print('ATTENTION : hight calibrator change detected!!')

    # print(f'Detected a difference of {difference} %')
    # print(f'{previous_value} --> {current_value}')

    return abs(difference)

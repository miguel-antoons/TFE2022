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


def detect_noise_variations(y_data, current_noise):
    mean_noise = np.mean(y_data)
    std_dev_noise = np.std(y_data)

    reference_deviation = 3.2 * std_dev_noise

    if current_noise >= (mean_noise + reference_deviation):
        return 1
    elif current_noise <= (mean_noise - reference_deviation):
        return -1
    else:
        return 0


def detect_noise_variations2(y_data, current_noise):
    q1 = np.percentile(y_data, 25, interpolation='lower')
    q3 = np.percentile(y_data, 75, interpolation='higher')

    interquartile = q3 - q1

    upper_limit = q3 + (2.4 * interquartile)
    lower_limit = q1 - (2.4 * interquartile)

    if current_noise >= upper_limit:
        return 1
    elif current_noise <= lower_limit:
        return -1
    else:
        return 0


def detect_calibrator_variations(y_data, current_calibrator):
    mean_calibrator = np.mean(y_data)
    std_dev_calibrator = np.std(y_data)

    reference_deviation = 3.5 * std_dev_calibrator

    if current_calibrator >= (mean_calibrator + reference_deviation):
        return 1
    elif current_calibrator <= (mean_calibrator - reference_deviation):
        return -1
    else:
        return 0


def detect_calibrator_variations2(y_data, current_calibrator):
    q1 = np.percentile(y_data, 25, interpolation='lower')
    q3 = np.percentile(y_data, 75, interpolation='higher')

    interquartile = q3 - q1

    upper_limit = q3 + (2.5 * interquartile)
    lower_limit = q1 - (2.5 * interquartile)

    if current_calibrator >= upper_limit:
        return 1
    elif current_calibrator <= lower_limit:
        return -1
    else:
        return 0


def mad(array):
    median = np.median(array)
    return median, np.median(np.abs(array - median))

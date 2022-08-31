import numpy as np

from scipy.optimize import curve_fit


def fit_func(x, a, b):
    # * currently not used
    x = np.array(x)
    return a * x + b


def detect_noise_decrease(x_data, y_data, index, interval=150):
    # * currently not used
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
    # * currently not used
    if current_value > previous_value * 10:
        # print(f'A significative noise increase at index {current_index}')
        return True

    return False


def detect_noise_variations_old(y_data, current_noise):
    """
    * currently not used
    This function detects high noise variations. It does so by calculating the
    mean and the standard deviation. From those 2 values it creates an upper
    and lower limit. Each noise value that goes beyond those limits will be
    communicated.

    Parameters
    ----------
    y_data : np.array
        numpy array from which the mean and standard deviation will be
        calculated
    current_noise : decimal.Decimal
        The new noise value

    Returns
    -------
    int
        1 if there is a high increase, -1 if there is a high decrease, 0 if
        everything is normal
    """
    mean_noise = np.mean(y_data)
    std_dev_noise = np.std(y_data)

    # calculate the limits deviation from the mean
    reference_deviation = 3.2 * std_dev_noise

    if current_noise >= (mean_noise + reference_deviation):
        return 1
    elif current_noise <= (mean_noise - reference_deviation):
        return -1
    else:
        return 0


def detect_noise_variations(y_data, current_noise):
    """
    This function detects high noise variations. It does so by calculating the
    interquartile. From that value it creates an upper and lower limit. Each
    noise value that goes beyond those limits will be communicated.

    Parameters
    ----------
    y_data : np.array
        numpy array from which interquartile calculated
    current_noise : decimal.Decimal
        The new noise value

    Returns
    -------
    int
        1 if there is a high increase, -1 if there is a high decrease, 0 if
        everything is normal
    """
    # get 25th and 75th percentile
    q1 = np.percentile(y_data, 25, interpolation='lower')
    q3 = np.percentile(y_data, 75, interpolation='higher')

    interquartile = float(q3 - q1)

    # calculate the upper and lower limits
    upper_limit = q3 + (6.0 * interquartile)
    lower_limit = q1 - (1.5 * interquartile)

    if current_noise >= upper_limit:
        return 1
    elif current_noise <= lower_limit or current_noise <= 0:
        return -1
    else:
        return 0


def detect_calibrator_variations_old(y_data, current_calibrator):
    """
    * currently not used
    This function detects high calibrator variations. It does so by
    calculating the mean and the standard deviation. From those 2 values it
    creates an upper and lower limit. Each calibrator value that goes beyond
    those limits will be communicated.

    Parameters
    ----------
    y_data : np.array
        numpy array from which the mean and standard deviation will be
        calculated
    current_calibrator : decimal.Decimal
        The new calibrator value

    Returns
    -------
    int
        1 if there is a high increase, -1 if there is a high decrease, 0 if
        everything is normal
    """
    mean_calibrator = np.mean(y_data)
    std_dev_calibrator = np.std(y_data)

    # calculate the limits deviation from the mean
    reference_deviation = 3.5 * std_dev_calibrator

    if current_calibrator >= (mean_calibrator + reference_deviation):
        return 1
    elif current_calibrator <= (mean_calibrator - reference_deviation):
        return -1
    else:
        return 0


def detect_calibrator_variations(y_data, current_calibrator):
    """
    This function detects high calibrator variations. It does so by
    calculating the interquartile. From that value it creates an upper and
    lower limit. Each calibrator value that goes beyond those limits will be
    communicated.

    Parameters
    ----------
    y_data : np.array
        numpy array from which interquartile calculated
    current_calibrator : decimal.Decimal
        The new calibrator value

    Returns
    -------
    int
        1 if there is a high increase, -1 if there is a high decrease, 0 if
        everything is normal
    """
    # get 25th and 75th percentile
    q1 = np.percentile(y_data, 20, interpolation='lower')
    q3 = np.percentile(y_data, 80, interpolation='higher')

    interquartile = float(q3 - q1)

    # calculate upper and lower limits
    upper_limit = q3 + (2.5 * interquartile)
    lower_limit = q1 - (2.0 * interquartile)

    if current_calibrator >= upper_limit:
        return 1
    elif current_calibrator <= lower_limit or current_calibrator <= 0:
        return -1
    else:
        return 0


def mad(array):
    # * currently not used
    median = np.median(array)
    return median, np.median(np.abs(array - median))

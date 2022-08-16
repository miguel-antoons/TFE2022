import simplejson as json
import numpy as np


def get_key_value(key, dict_list, sys_id=False):
    if sys_id:
        return [
            dictionnary[key]
            for dictionnary in dict_list
            if dictionnary['system_id'] == sys_id
        ]
    else:
        return [dictionnary[key] for dictionnary in dict_list]


def mad(array):
    median = np.median(array)
    return median, np.median(np.abs(array - median))


def calc_median(json_path):
    file_data = {}
    with open(json_path, 'r') as raw_data:
        file_data = json.load(raw_data)

    sys_ids = list(dict.fromkeys(get_key_value('system_id', file_data)))
    print(sys_ids)

    for sys_id in sys_ids:
        noise = get_key_value('noise_psd', file_data, sys_id)
        calibrator = get_key_value('calibrator_psd', file_data, sys_id)

        median_noise, mad_noise = mad(noise)
        mean_noise = np.mean(noise)
        std_dev_noise = np.std(noise)
        variance_noise = np.var(noise)

        median_calibrator, mad_calibrator = mad(calibrator)
        mean_calibrator = np.mean(calibrator)
        std_dev_calibrator = np.std(calibrator)
        variance_calibrator = np.var(calibrator)

        print(f'\n------ ID {sys_id} ------')
        print(f'Median noise :\t\t\t {median_noise}')
        print(f'Mad noise :\t\t\t {mad_noise}')
        print(f'Mean noise :\t\t\t {mean_noise}')
        print(f'Standard deviation noise :\t {std_dev_noise}')
        print(f'Variance noise : \t\t {variance_noise}')

        print(f'Median calibrator :\t\t {median_calibrator}')
        print(f'Mad calibrator :\t\t {mad_calibrator}')
        print(f'Mean calibrator :\t\t {mean_calibrator}')
        print(f'Standard deviation calibrator :\t {std_dev_calibrator}')
        print(f'Variance calibrator :\t\t {variance_calibrator}')


if __name__ == '__main__':
    calc_median('/home/niutalol/Downloads/file_data_2022-06-01.json')

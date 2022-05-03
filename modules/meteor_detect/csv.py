import csv
import os


def write_csv(
    data,
    directory=None,
    filename='meteor_detect',
    header=[
        'location_code',
        'antenna_id',
        'file_start',
        'meteor_count',
        'meteor_time',
        'fmin',
        'fmax',
        'distance_km'
    ]
):
    if directory is None:
        directory = os.getcwd()

    addition = ''
    i = 0
    while (filename + addition + '.csv') in os.listdir(directory):
        i += 1
        addition = f' ({i})'

    filename += addition
    filename += '.csv'
    file_path = os.path.join(directory, filename)

    with open(file_path, mode='w') as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            fieldnames=header
        )

        for loc_code in data.keys():
            for antenna in data[loc_code].keys():
                for date in data[loc_code][antenna].keys():
                    for meteor in data[loc_code][antenna]['meteors']:
                        csv_writer.writerow(
                            [
                                loc_code,
                                antenna,
                                date,
                                len(data[loc_code][antenna][date]),
                                meteor['t'],
                                meteor['f_min'],
                                meteor['f_max'],
                                data[loc_code]['distance']
                            ]
                        )

import csv
import os

from datetime import datetime, timezone, timedelta
from typing import Union


def write_csv(
    data: list,
    directory: Union[str, None] = None,
    filename: str = 'meteor_detect',
    header: list = [
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
    """
    Function writes a csv file with all the information from detected meteors

    Parameters
    ----------
    data : list
        list with all the data from the detected meteors
    directory : Union[str, None], optional
        directory in which to store the new csv file, by default None
    filename : str, optional
        name that the csv file will take, by default 'meteor_detect'
    header : list, optional
        header of the csv file
        , by default
            [
                'location_code',
                'antenna_id',
                'file_start',
                'meteor_count',
                'meteor_time',
                'fmin',
                'fmax',
                'distance_km'
            ]
    """
    if directory is None or directory == '':
        directory = os.getcwd()

    # add an addition to the filename if the filename already exists
    addition = ''
    i = 0
    while (filename + addition + '.csv') in os.listdir(directory):
        i += 1
        addition = f' ({i})'

    filename += addition
    filename += '.csv'
    file_path = os.path.join(directory, filename)

    # open the file in write mode
    with open(file_path, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )

        csv_writer.writerow(header)

        # add one line per detected meteor to the csv file
        for loc_code in data.keys():
            for antenna in data[loc_code]['sys'].keys():
                for date in data[loc_code]['sys'][antenna].keys():
                    file = data[loc_code]['sys'][antenna][date]
                    for meteor in file['meteors']:
                        seconds = (
                            file['start']
                            + float(meteor['t']) * 1000000
                        ) / 1000000
                        microseconds = (seconds % 1) * 1000000
                        meteor_date = datetime.fromtimestamp(
                            int(seconds),
                            tz=timezone.utc
                        )
                        meteor_date += timedelta(
                            microseconds=int(microseconds))
                        csv_writer.writerow(
                            [
                                loc_code,
                                antenna,
                                date,
                                len(file['meteors']),
                                meteor_date.strftime('%Y-%m-%dT%H:%M:%S:%f'),
                                meteor['f_min'],
                                meteor['f_max'],
                                data[loc_code]['distance']
                            ]
                        )
        print(file_path)

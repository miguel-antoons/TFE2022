import os

from datetime import datetime
from ..database import database as db


def verify_archive_date(search_date, parent_directory):
    dir_content = os.listdir(parent_directory)

    if (year := search_date.strftime('%Y')) not in dir_content:
        return False

    directory = os.path.join(parent_directory, year)
    dir_content = os.listdir(directory)

    if (month := search_date.strftime('%m')) not in dir_content:
        return False

    directory = os.path.join(directory, month)
    dir_content = os.listdir(directory)

    if (day := search_date.strftime('%d')) not in dir_content:
        return False

    return {
        "path": os.path.join(directory, day),
        "content": os.listdir(os.path.join(directory, day))
    }


def get_archived_files(precise_time, station_ids, parent_directory):
    if not (directory := verify_archive_date(precise_time, parent_directory)):
        return False

    database_request_data = []

    for filename in directory['content']:
        split_filename = filename.split('_')

        # get date and time of the file
        file_date = datetime.strptime(
            f'{split_filename[2]} {split_filename[3]}',
            '%Y%m%d %H%M'
        )
        file_path = os.path.join(directory['path'], filename)

        if (
            os.path.isfile(file_path)
            and file_date > (precise_time - datetime.timedelta(min=1))
            and file_date < (precise_time + datetime.timedelta(min=6))
            and split_filename[4] in station_ids.keys()
        ):
            database_request_data.append({
                "station_code": split_filename[4],
                "file_path": file_path,
                "time": file_date.strftime('%Y-%m-%d %H:%M'),
                "datetime": file_date,
                "system_id": (
                    station_ids
                    [split_filename[4]]
                    [str(int(
                        split_filename[5]
                        .replace('SYS', '')
                        .replace('.wav', '')
                    ))]
                )
            })

if __name__ == '__main__':
    print(datetime.fromtimestamp(1312189216461538 // 1000000).strftime('%Y-%m-%d %H:%M:%S'))

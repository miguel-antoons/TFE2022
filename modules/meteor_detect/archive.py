import os

from datetime import datetime


def verify_archive_date(search_date, parent_directory):
    dir_content = os.listdir(parent_directory)

    year = search_date.strftime('%Y')
    if year not in dir_content:
        return parent_directory

    directory = os.path.join(parent_directory, year)
    dir_content = os.listdir(directory)

    month = search_date.strftime('%m')
    if month not in dir_content:
        return directory

    directory = os.path.join(directory, month)
    dir_content = os.listdir(directory)

    day = search_date.strftime('%d')
    if day not in dir_content:
        return directory

    return {
        "path": os.path.join(directory, day),
        "content": os.listdir(os.path.join(directory, day))
    }


def get_archived_files(requested_files, precise_time, parent_directory):
    directory = verify_archive_date(precise_time, parent_directory)
    if not directory:
        return False

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
            and split_filename[4] in requested_files.keys()
        ):
            antenna = str(int(
                split_filename[5]
                .replace('SYS', '')
                .replace('.wav', '')
            ))
            if antenna in requested_files[split_filename[4]]['sys'].keys():
                system = requested_files[split_filename[4]]['sys'][antenna]
                date = file_date.strftime('%Y%m%d%H%M')
                if date in system.keys():
                    system[date]["file_path"] = file_path

    return requested_files


# if __name__ == '__main__':
#     print(get_archived_files(
#         {
#             'BEGRIM': {
#                 '1': {
#                     '202204231055': {
#                         'start': 1647341699673655,
#                         'end': 1647341999671442,
#                         'date': datetime(2022, 4, 23, 10, 55)
#                     },
#                     '202204231100': {
#                         'start': 1647341999671660,
#                         'end': 1647342299669398,
#                         'date': datetime(2022, 4, 23, 11, 0)
#                     }
#                 }
#             },
#             'BEHAAC': {
#                 '1': {
#                     '202204231055': {
#                         'start': 1647341701695598,
#                         'end': 1647342001700517,
#                         'date': datetime(2022, 4, 23, 10, 55)
#                     },
#                     '202204231100': {
#                         'start': 1647342001700496,
#                         'end': 1647342301705364,
#                         'date': datetime(2022, 4, 23, 11, 0)
#                     }
#                 }
#             }
#         },
#         datetime(2022, 4, 23),
#         'recordings/'
#     ))

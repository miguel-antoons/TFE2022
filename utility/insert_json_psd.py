import simplejson as json
import sys


def insert_json(file_path):
    file_data = {}
    with open(file_path, 'r') as raw_data:
        file_data = json.load(raw_data)

    print(file.insert_psd(file_data))


if __name__ == '__main__':
    sys.path.insert(0, 'modules')
    from database import file
    insert_json('/home/niutalol/Downloads/file_data_2022-06-01.json')

#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import datetime
import gzip
import os
import re
from collections import namedtuple
from time import strptime, strftime

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

field_names = [
            'remote_addr', 'remote_user', 'http_x_real_ip', '[time_local]', 'request',
            'status', 'body_bytes_sent', 'http_referer', 'http_user_agent', 'http_x_forwarded_for',
            'http_X_REQUEST_ID', 'http_X_RB_USER', 'request_time'
            ]

ACCEPTABLE_ARCHIVE_TYPES = ['gz']

File = namedtuple('File', 'path date is_archived')


def check_file_exist(path: str) -> bool:
    # print(os.path.exists(path))
    return os.path.exists(path)


def check_fresh_logfile_name(path: str = 'logs') -> File:
    files_names = []
    latest_date = strptime('0001-01-01', '%Y-%m-%d')
    latest_path = ''
    is_archived = False
    for _, _, files in os.walk(path):
        files_names.append(files)
    for name in files_names[0]:
        date = re.search(r'\d{8}', str(name))
        cleaned_date = strptime(date[0], '%Y%m%d')
        if cleaned_date > latest_date:
            latest_date = cleaned_date
            latest_path = name
            # print('latest_path===>', latest_path)
            archived = check_if_file_is_gz_archived(name)
            if not archived == (True, True):
                continue
            is_archived = archived
            # TODO: все равно тащит gz2 архив
    print(File(latest_path, latest_date, is_archived))
    return File(latest_path, latest_date, is_archived)


def save_success_state():
    pass


def check_if_file_is_gz_archived(filename: str) -> (bool, bool):

    # unarchived_pattern = re.search(r'\.{1}(log-)\d{8}', filename)
    archived_pattern = re.search(r'\.{1}(log-)\d{8}\.{1}(?:gz$)', filename)
    if archived_pattern and archived_pattern.split('.')[2] in ACCEPTABLE_ARCHIVE_TYPES:
        return True, True
    return False, False


def check_for_external_config():
    pass


def process_gzipped_files(filename: str ='logs/nginx-access-ui.log-20170630.gz') -> list:
    result = []
    with gzip.open(filename, 'rb') as log_file:
        for line in log_file.readlines()[:3]:
            result.append(line.decode().split(' '))
            # print(line.decode().split(' '))

    return result


def main():
    check_fresh_logfile_name()
    check_file_exist('logs/nginx-access-ui.log-20170630.gz')



if __name__ == "__main__":
    main()


"""
1. Проверить, что название файла соответствует целевому.
2. Проверить, архивный ли файл или нет. 
"""
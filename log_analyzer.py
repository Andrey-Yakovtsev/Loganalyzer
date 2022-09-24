#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import argparse
import datetime
import gzip
import logging
import os
import re
from collections import namedtuple
from time import strptime

logging.basicConfig(

    level=logging.DEBUG,
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
    )

logger = logging.getLogger('Log_analyzer')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
# ch = logging.FileHandler(filename=f'{datetime.datetime.now()}.log', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

LOCAL_CONFIG = {
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
SERVICES_TO_MONITOR = ['nginx_access_ui']

File = namedtuple('File', 'path date is_archived')


def check_fresh_logfile_name(path: str = 'log') -> File:
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
            logging.info(f'latest_path===> {latest_path}')
            is_archived = check_if_file_is_gz_archived(name)
            if not is_archived:
                # FIXME gz2-архивы пролезают...
                logging.info(f'{name} is not archeved file - skipping')
                continue
    logging.info(f'{File(latest_path, latest_date, is_archived)}')
    return File(latest_path, latest_date, is_archived)


def html_report_exists(date, reports_dir: str = LOCAL_CONFIG.get('REPORT_DIR')) -> bool:
    files_names = []
    latest_date = strptime('0001-01-01', '%Y-%m-%d')
    for _, _, files in os.walk(reports_dir):
        files_names.append(files)
    for name in files_names[0]:
        date = re.search(r'\d{4}.\d{2}.\d{2}', str(name))
        cleaned_date = strptime(date[0], '%Y.%m.%d')
        if cleaned_date > latest_date:
            latest_date = cleaned_date
    if not latest_date == date:
        return False

    return True


def check_log_is_fresh_and_unprocessed(date) -> bool:
    """Проверяет, что дата лога сегодняшняя и что отчета с такой датой нет в папке /reports"""
    # today = strptime(strftime(str(datetime.datetime.today()).split(' ')[0]), '%Y-%m-%d')
    today = strptime('2017-06-29', '%Y-%m-%d')  # mocked today )))
    if date == today and not html_report_exists(date):
        logging.warning("Today's log already processed. Skipping")
        return True
    logging.info("Moving to report generation............")
    return False


def check_if_file_is_gz_archived(filename: str) -> bool:
    # unarchived_pattern = re.search(r'\.{1}(log-)\d{8}', filename)
    archived_pattern = re.search(r'\.{1}(log-)\d{8}\.{1}(?:gz$)', filename)
    if archived_pattern and (archived_pattern.string.split('.')[2] in ACCEPTABLE_ARCHIVE_TYPES):
        logging.info('Filename appeared to be a proper "gz"-type')
        return True
    logging.info('Filename appeared to be not a proper "gz"-type')
    return False


def check_if_nginx_log(filename: str) -> bool:
    return filename.split('.')[0] == 'nginx-access-ui'


def process_config() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_file_path', type=str, help='Path to confin file')
    args = parser.parse_args()
    if not args.config_file_path:
        logger.debug('Using local config')
        return LOCAL_CONFIG
    else:
        logger.debug('Using external config')
        with open(args.config_file_path) as config_file:
            for line in config_file.readlines():
                #modifying LOCAL_CONFIG in place
                LOCAL_CONFIG[line.split('=')[0]] = line.split('=')[1]
            return LOCAL_CONFIG


def process_file(filename: str ='nginx-access-ui.log-20170630.gz', is_archived: bool=False, config_source=LOCAL_CONFIG) -> list:
    result = []
    if is_archived:
        logger.info('Processing GZipped file')
        with gzip.open(f'{config_source.get("LOG_DIR", "log")}/{filename}', 'rb') as log_file:
            for line in log_file.readlines()[:3]:
                result.append(line.decode().split(' '))
                logger.debug(line.decode().split(' '))
    else:
        logger.info('Processing plain file')
        with open(f'{config_source.get("LOG_DIR", "log")}/{filename}', 'rb') as log_file:
            for line in log_file.readlines()[:3]:
                result.append(line.decode().split(' '))
                logger.debug(line.decode().split(' '))

    return result


def main():
    filename, date, is_archived = check_fresh_logfile_name()
    if not check_if_nginx_log(filename):
        logging.warning(f'{filename} is not an NGINX log. Skipping')
        return
    if not check_log_is_fresh_and_unprocessed(date):
        process_file(filename, is_archived, config_source=process_config())
        return
    logging.debug(f'Report for {date} already PROCESSED!!!!. Skipping')


if __name__ == "__main__":
    main()


"""


Проверить, что архив нужного имени, а не какой-нить bz2 << === ПОФИКСИТЬ

Функция, которая парсит лог д.б. генератором 

###
Мониторинг
logging - 3 уровня.
Путь к логам в конфиге. Если там не указан, то вывод в СТДАут
На неожиданные ошибки - трейсбек Логгинга

###
тесты - не забыть...
 
"""
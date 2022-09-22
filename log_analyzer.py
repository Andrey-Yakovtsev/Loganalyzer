#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import datetime
import gzip
import logging
import os
import re
from collections import namedtuple
from time import strptime, strftime


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

# add ch to logger
logger.addHandler(ch)

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
SERVICES_TO_MONITOR = ['nginx_access_ui']
REPORT_LOGS_DIR = 'report'

File = namedtuple('File', 'path date is_archived')


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
            logging.info(f'latest_path===> {latest_path}')
            is_archived = check_if_file_is_gz_archived(name)
            if not is_archived:
                # FIXME gz2-архивы пролезают...
                logging.info(f'{name} is not archeved file - skipping')
                continue
    logging.info(f'{File(latest_path, latest_date, is_archived)}')
    return File(latest_path, latest_date, is_archived)


def report_exists(date) -> bool:
    files_names = []
    latest_date = strptime('0001-01-01', '%Y-%m-%d')
    for _, _, files in os.walk(REPORT_LOGS_DIR):
        files_names.append(files)
    for name in files_names[0]:
        date = re.search(r'\d{8}', str(name))
        cleaned_date = strptime(date[0], '%Y%m%d')
        if cleaned_date > latest_date:
            latest_date = cleaned_date
    if not latest_date == date:
        return False

    return True


def check_log_is_fresh_and_unprocessed(date) -> bool:
    """Проверяет, что дата файла сегодняшняя и что отчета с такой датой нет в папке отчеты"""
    # TODO Не могу сфокусироваться что тут проверяем...
    yesturday = strptime(strftime(str(datetime.datetime.today() \
                                       - datetime.timedelta(days=1)).split(' ')[0]), '%Y-%m-%d')
    today = strptime(strftime(str(datetime.datetime.today()).split(' ')[0]), '%Y-%m-%d')
    # сегодняшний лог существует и отчет уже есть
    if date == today and not report_exists(date):
        # TODO тут остановился - на поиске отчета готового
        logging.warning("Today's log already processed. Breaking operation")
        return True


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


def check_for_external_config():
    pass


def process_file(filename: str ='nginx-access-ui.log-20170630.gz', is_archived: bool=False) -> list:
    result = []
    if is_archived:
        logger.info('Processing GZipped file')
        with gzip.open(f'logs/{filename}', 'rb') as log_file:
            for line in log_file.readlines()[:3]:
                result.append(line.decode().split(' '))
                logger.debug(line.decode().split(' '))
    else:
        logger.info('Processing plain file')
        with open(f'logs/{filename}', 'rb') as log_file:
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
        return
    # process_file(filename, is_archived)


if __name__ == "__main__":
    main()


"""

Может оказаться, что свежих нет - не является ошибкой
Проверить, что архив нужного имени, а не какой-нить bz2

Если удачно отработал - работу не переделывает (проверить по наличию файла отчета с текущей датой)
Добавить --config-арг с указанием пути на конфиг-файл.
Конфиги сливаются с приоритетом файлового (м.б. пустым)
Функция, которая парсит лог д.б. генератором

###
Мониторинг
logging - 3 уровня.
Путь к логам в конфиге. Если там не указан, то вывод в СТДАут
На неожиданные ошибки - трейсбек Логгинга

###
тесты - не забыть...
 
"""
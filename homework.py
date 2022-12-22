import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRAC_TOKEN')
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = 1679364340

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    level=logging.CRITICAL)


def check_tokens():
    """Проверка доступности переменных окружения."""
    for key in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        if key is None:
            logging.critical('Отсутствуют переменные окружения')
            return False
    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(f'не получилось отправить сообщение: {error}')
    logging.debug('Отправили сообщение')


def get_api_answer(timestamp):
    """Делает запрос к API."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != 200:
        raise Exception('Ошибка при запросе к основному API '
                        f'{response.status_code}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    global gethomework
    try:
        gethomework = response.get('homeworks')
    except Exception as error:
        logging.error(f'Не найдена информация о домашке в API: {error}')
    if isinstance(gethomework, dict):
        raise TypeError('Получен ответ не в виде списка')
    elif 'homeworks' not in response:
        raise TypeError('Не найден ключ homeworks')
    return response.get('homeworks')[0]


def parse_status(homework):
    """Извлекает статусы домашней работы."""
    try:
        homework_name = homework.get('homework_name')
        verdict = HOMEWORK_VERDICTS[homework.get('status')]
    except Exception as error:
        logging.error(f'Не наден статус домашней работы: {error}')
    if 'homework_name' not in homework:
        raise TypeError('Нету имени домашней работы')
    elif 'status' not in homework:
        raise TypeError('У домашней работы нету статуса')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise ValueError('Отсутствую глобальные переменные')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            if check_response(response):
                message = parse_status(check_response(response))
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
            continue


if __name__ == '__main__':
    main()

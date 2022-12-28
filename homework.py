import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRAC_TOKEN')
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s'
))
logger.addHandler(handler)


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    return all(tokens)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logging.error(f'не получилось отправить сообщение: {error}')
    else:
        logging.debug('Отправили сообщение')


def get_api_answer(timestamp):
    """Делает запрос к API."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
    except requests.exceptions.RequestException as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise ConnectionError(
            f'Ошибка соединения {response.status_code}')
    try:
        return response.json()
    except requests.exceptions.InvalidJSONError as error:
        logging.error(f'Ошибка получения json: {error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if isinstance(response, list):
        raise TypeError('Получен неправильный тип данных - ожидаемый (list)')
    elif isinstance(response.get('homeworks'), dict):
        raise TypeError('Получен неправильный тип данных - ожидаемый (dict)')
    elif 'homeworks' not in response:
        raise KeyError("Отсутствует ключ 'homeworks' с домашками")
    elif 'current_date' not in response:
        raise KeyError("API не вернуло текущую дату")
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает статусы домашней работы."""
    if homework.get('status') not in HOMEWORK_VERDICTS.keys():
        raise NameError("Неизвестный статус домашней работы - "
                        f"{homework.get('status')}")
    if 'homework_name' not in homework:
        raise KeyError('Нету имени домашней работы')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS[homework.get('status')]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствуют переменные окружения')
        raise ValueError('Добавьте переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            timestamp = get_api_answer(int(time.time())).get('current_date')
            response = get_api_answer(timestamp)
            gethomework = check_response(response)
            if 'homework_name' in gethomework[0]:
                message = parse_status(gethomework[0])
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(f'Ошибка при запросе к основному API: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

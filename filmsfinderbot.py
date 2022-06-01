import os
import sys
import requests
import telebot

from telebot import types
from random import randint, choice
from dotenv import load_dotenv


load_dotenv()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KINOPOISK = os.environ.get('API_TOKEN')
ENDPOINT_FILMS = os.environ.get('ENDPOINT_FILMS')
URL_PARAMS = {'token': API_KINOPOISK}
bot = telebot.TeleBot(TELEGRAM_TOKEN)


def check_tokens():
    """Проверяем наличие необходимых токенов."""
    if (
        TELEGRAM_TOKEN is None
        or API_KINOPOISK is None
        or ENDPOINT_FILMS is None
    ):
        return False
    return True


@bot.message_handler(commands=['start'])
def start_up(data):
    """Стартовое приветствие пользователя.
    Создание и сохранение пользователя."""
    name = data.chat.first_name
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Найти случайный фильм')
    item2 = types.KeyboardButton('Фильтр: рейтинг КиноПоиска')
    item3 = types.KeyboardButton('Фильтр: рейтинг IMDB')
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    bot.send_message(
        data.chat.id,
        f'Здравствуйте, {name}!\nЯ - Films Finder Bot\nБот для поиска фильмов к просмотру на вечер!\n'
         'На данный момент я могу найти и предложить к просмотру любой случайный фильм,\n'
         'так же можно задать фильтрацию фильмов по рейтингу на Кинопоиске, либо IMDB =)', reply_markup=markup
    )


def get_rdm_rating_imdb(data):
    rtg = data.text.split(' ')
    chat_id = data.chat.id
    min_rtg = int(rtg[0])
    max_rtg = int(rtg[1])
    film_list = f'limit=100&field=rating.imdb&search={min_rtg}-{max_rtg}&field=rating.kp&search=1-10'
    middle_endpoint = ENDPOINT_FILMS + f'?{film_list}'
    pages = requests.get(middle_endpoint, params=URL_PARAMS).json().get('pages')
    rdm_page = randint(1, pages)
    final_endpoint = ENDPOINT_FILMS + f'?{rdm_page}&' + film_list
    response = requests.get(final_endpoint, params=URL_PARAMS).json()
    response = choice(response.get('docs'))
    send_message(response, chat_id)


def get_rdm_rating_kp(data):
    rtg = data.text.split(' ')
    chat_id = data.chat.id
    min_rtg = int(rtg[0])
    max_rtg = int(rtg[1])
    film_list = f'limit=100&field=rating.kp&search={min_rtg}-{max_rtg}'
    middle_endpoint = ENDPOINT_FILMS + f'?{film_list}'
    pages = requests.get(middle_endpoint, params=URL_PARAMS).json().get('pages')
    rdm_page = randint(1, pages)
    final_endpoint = ENDPOINT_FILMS + f'?{rdm_page}&' + film_list
    response = requests.get(final_endpoint, params=URL_PARAMS).json()
    response = choice(response.get('docs'))
    send_message(response, chat_id)


def get_random_film(id):
    rdm_page = randint(1, 682)
    film_list = 'limit=100&field=rating.kp&search=5-10'
    final_endpoint = ENDPOINT_FILMS + f'?{rdm_page}&' + film_list
    response = requests.get(final_endpoint, params=URL_PARAMS).json()
    response = choice(response.get('docs'))
    send_message(response, id)


def send_message(film, chat_id):
    msg_name = film.get('name')
    poster_url = film.get('poster').get('url')
    msg_description = film.get('shortDescription')
    if msg_description is None:
        msg_description = film.get('description')
    rating_kp = film.get('rating').get('kp')
    rating_imdb = film.get('rating').get('imdb')
    text = (
        f'{msg_name}\n'
        f'IMDB: {rating_imdb}\n'
        f'KP: {rating_kp}\n\n'
        f'Описание: {msg_description}'
    )
    bot.send_photo(chat_id, poster_url)
    bot.send_message(chat_id, text)


@bot.message_handler(content_types=['text'])
def send_random_film(data):
    chat_id = data.chat.id
    if data.text.strip().lower() == 'найти случайный фильм':
        get_random_film(chat_id)
    elif data.text.strip().lower() == 'фильтр: рейтинг кинопоиска':
        msg = bot.send_message(chat_id, 'Введите диапазон искомого рейтинга через пробел\nНапример: 5 9')
        bot.register_next_step_handler(msg, get_rdm_rating_kp)
    elif data.text.strip().lower() == 'фильтр: рейтинг imdb':
        msg = bot.send_message(chat_id, 'Введите диапазон искомого рейтинга через пробел\nНапример: 5 9')
        bot.register_next_step_handler(msg, get_rdm_rating_imdb)


def main():
    if not check_tokens():
        print('Отсутствуют переменная (-ные) окружения!')
        return 0
    bot.enable_save_next_step_handlers(delay=2, filename='./handlers-save/step.save')
    bot.load_next_step_handlers()
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
        sys.exit(0)

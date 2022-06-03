import os
import sys
import requests
import telebot

from keyboards import *
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
    bot.send_message(
        data.chat.id,
        f'Здравствуйте, {name}!\nЯ - Films Finder Bot\nБот для поиска фильмов к просмотру на вечер!\n'
         'На данный момент я могу найти и предложить к просмотру любой случайный фильм,\n'
         'так же можно задать фильтрацию фильмов по рейтингу на Кинопоиске, либо IMDB =)', reply_markup=main_keyboard
    )


# получение случайного фильма с фильтром по жанру
def get_film_filter_genre(data):
    try:
        bot.send_chat_action(data.chat.id, action='typing')
        genre = data.text.strip().lower()
        print(f'Запрашиваемый жанр: {genre}')
        film_list = f'limit=100&field=rating.imdb&search=1-10&field=rating.kp&search=6-10&search={genre}&field=genres.name&search=1&field=typeNumber&field=year&search=2000-2022'
        middle_endpoint = ENDPOINT_FILMS + f'?{film_list}'
        pages = requests.get(middle_endpoint, params=URL_PARAMS).json().get('pages')
        rdm_page = randint(1, pages)
        final_endpoint = ENDPOINT_FILMS + f'?{rdm_page}&' + film_list
        response = requests.get(final_endpoint, params=URL_PARAMS).json()
        while response.get('description') is None:
            response = choice(response.get('docs'))
        send_message(response, data.chat.id)
    except:
        bot.send_message(chat_id=data.chat.id, text='Что-то пошло не так. Удостоверьтесь, что жанр написан верно.', reply_markup=main_keyboard)


# получение случайного фильма с фильтром по рейтингу кинопоиска или IMDB
def get_film_filter_rating_kp_or_imdb(data, source):
    chat_id = data.chat.id
    try:
        bot.send_chat_action(chat_id, action='typing')
        rtg = data.text.split(' ')
        min_rtg = int(rtg[0])
        max_rtg = int(rtg[1])
        if source == 'kp':
            film_list = f'limit=100&field=rating.kp&search={min_rtg}-{max_rtg}&field=rating.imdb&search=1-10&search=1&field=typeNumber'
        elif source == 'imdb':
            film_list = f'limit=100&field=rating.imdb&search={min_rtg}-{max_rtg}&field=rating.kp&search=1-10&search=1&field=typeNumber'
        middle_endpoint = ENDPOINT_FILMS + f'?{film_list}'
        pages = requests.get(middle_endpoint, params=URL_PARAMS).json().get('pages')
        rdm_page = randint(1, pages)
        final_endpoint = ENDPOINT_FILMS + f'?page={rdm_page}&' + film_list
        response = requests.get(final_endpoint, params=URL_PARAMS).json()
        response = choice(response.get('docs'))
        while response.get('description') is None:
            response = choice(response.get('docs'))
        send_message(response, chat_id)
    except:
        msg = bot.send_message(
            data.chat.id,
            ('Неверно введено значение! Необходимо ввести сначала минимальный, затем максимальный рейтинг одним сообщением через пробел.\n'
             'Попробуйте еще раз.'),
        )
        bot.register_next_step_handler(msg, get_film_filter_rating_kp_or_imdb, source)


# получение случайного фильма
def get_random_film(id):
    rdm_page = randint(1, 403)
    film_list = 'limit=100&field=rating.kp&search=5-10&field=year&search=2000-2022'
    final_endpoint = ENDPOINT_FILMS + f'?{rdm_page}&' + film_list
    response = requests.get(final_endpoint, params=URL_PARAMS).json()
    while response.get('description') is None:
        response = choice(response.get('docs'))
    send_message(response, id)


# отправка сообщения пользователю
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
    bot.send_message(chat_id, text, reply_markup=main_keyboard)
    print(f'Фильм успешно получен: {msg_name}')


# ожидание команды и вызов дальнейших инструкций
@bot.message_handler(content_types=['text'])
def send_random_film(data):
    chat_id = data.chat.id
    if data.text.strip().lower() == 'найти случайный фильм':
        bot.send_chat_action(chat_id, action='typing')
        print('Запрос случайного фильма')
        get_random_film(chat_id)
    elif data.text.strip().lower() == 'фильтры':
        bot.send_message(chat_id, 'Выберите фильтр', reply_markup=keyboard_filters)
    elif data.text.strip().lower() == 'рейтинг кинопоиска':
        msg = bot.send_message(chat_id, 'Введите диапазон искомого рейтинга через пробел\nНапример: 5 9')
        print('Запрос по рейтингу КП')
        source = 'kp'
        bot.register_next_step_handler(msg, get_film_filter_rating_kp_or_imdb, source)
    elif data.text.strip().lower() == 'рейтинг imdb':
        source = 'imdb'
        msg = bot.send_message(chat_id, 'Введите диапазон искомого рейтинга через пробел\nНапример: 5 9')
        print('Запрос по рейтингу IMDB')
        bot.register_next_step_handler(msg, get_film_filter_rating_kp_or_imdb, source)
    elif data.text.strip().lower() == 'жанр':
        msg = bot.send_message(chat_id, 'Выберите жанр', reply_markup=keyboard_genres)
        bot.register_next_step_handler(msg, get_film_filter_genre)
        print('Запрос по жанру')
    else:
        bot.send_message(chat_id, 'Неизвестная команда =(')


def main():
    if not check_tokens():
        print('Отсутствуют переменная (-ные) окружения!')
        return 0
    print('Бот успешно запущен!')
    bot.enable_save_next_step_handlers(delay=2, filename='./handlers-save/step.save')
    bot.load_next_step_handlers()
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
        sys.exit(0)

import os
import sqlite3
# Импорт зависимостей из Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import traceback
import time
from datetime import datetime, timedelta
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
import re
import random
import requests
from dotenv import load_dotenv
# Импорт библиотеки по решению капчи
from vk_captcha import VkCaptchaSolver


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOCKEN")
DRIVER_PATH = os.getenv("DRIVER_PATH")
BINARY_LOCATION = os.getenv("BINARY_LOCATION")
ACCESS_TOKEN = os.getenv("SERVES_KEY")
version = "5.199"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_data = {}


def create_connection():
    return sqlite3.connect('vk_db.db')


bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Стартовая клавиатура
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [KeyboardButton(text="Залогиниться"),
           KeyboardButton(text="Собрать пользователей")]

main_keyboard.add(*buttons)


@bot.message_handler(commands=["start"])
def bot_start(message: Message):
    bot.send_message(
        message.chat.id,
        "Добрый день вы попали в бот по автолайкингу в VK",
        reply_markup=main_keyboard,
    )
    bot.send_message(
        message.chat.id, 'Для сбора пользователей нажмите кнопку "Собрать пользователей"')
    bot.send_message(
        message.chat.id, 'Для возможности расставить лайки или комментарии предварительно надо залогиниться')


@bot.message_handler(func=lambda message: message.text == "Залогиниться")
def auto_like(message: Message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    msg = bot.send_message(chat_id, "Введите ваш логин ВКонтакте:")
    bot.register_next_step_handler(msg, process_vk_id_step)


@bot.message_handler(
    func=lambda message: message.text == "Собрать пользователей")
def collect_user_groups(message: Message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    msg = bot.send_message(chat_id,
                           "Для сбора данных предварительно необходимо предоставить информацию")
    bot.register_next_step_handler(msg, request_group_info)


# Комментирование постов
comments_list = [
    "Отличный пост!",
    "Очень полезная информация, спасибо!",
    "Интересно, спасибо за пост!"
]


def get_random_comment():
    return random.choice(comments_list)


def comment_post(chat_id, driver, link):
    try:
        driver.get(link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, '_post_content')]")))

        # Функция для прокрутки страницы до тех пор, пока не появятся посты
        def scroll_until_posts_found(max_attempts=3):
            attempt = 0
            while attempt < max_attempts:
                post_contents = driver.find_elements(
                    By.XPATH, "//div[contains(@class, '_post_content')]")

                if post_contents:
                    return post_contents

                # Прокрутка страницы и ожидание загрузки контента
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                # Подождите, чтобы дать время для загрузки новых постов
                time.sleep(3)
                attempt += 1

            return []

        post_contents = scroll_until_posts_found()

        # Если посты не найдены после попыток прокрутки
        if not post_contents:
            bot.send_message(
                chat_id, f"Не удалось найти посты на странице: {link}")
            return

        for post_content in post_contents:
            try:
                # Проверка наличия кнопки комментирования
                comment_icon = post_content.find_element(
                    By.XPATH, ".//span[contains(@class, 'PostBottomAction__icon _comment_button_icon')]")

                # Проверка наличия и состояния кнопки
                if not comment_icon.is_displayed() or not comment_icon.is_enabled():
                    print("Иконка комментирования недоступна для клика, пропускаем.")
                    continue

                # Клик по кнопке комментирования
                driver.execute_script("arguments[0].click();", comment_icon)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'reply_field submit_post_field')]")))

                # Найти поле ввода комментария и отправить комментарий
                comment_field = post_content.find_element(
                    By.XPATH, ".//div[contains(@class, 'reply_field submit_post_field')]")
                comment_field.click()
                comment_field.send_keys(get_random_comment())

                # Найти и кликнуть кнопку отправки
                submit_button = post_content.find_element(
                    By.XPATH, ".//button[contains(@class, 'reply_send_button')]")
                driver.execute_script("arguments[0].click();", submit_button)

                bot.send_message(
                    chat_id, f"Комментарий поставлен на посте: {link}")
                # Дайте время для выполнения действия
                time.sleep(random.randint(5, 15))

            except Exception as e:
                print(f"Ошибка при попытке комментирования поста: {e}")
                bot.send_message(
                    chat_id, f"Ошибка при попытке комментирования поста: {e}")

    except Exception as e:
        error_message = f"Ошибка при обработке страницы {link}: {e}\n{traceback.format_exc()}"
        print(error_message)
        bot.send_message(chat_id, error_message)

    finally:
        driver.quit()


def process_comments(chat_id, driver):
    conn = sqlite3.connect('vk_db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT group_link FROM comment_group')
    groups = cursor.fetchall()
    conn.close()

    for group in groups:
        comment_post(chat_id, driver, group[0])


def create_comment_group_table(db_path='vk_db.db'):
    try:
        # Подключение к базе данных
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Создание таблицы, если она не существует
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comment_group (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_link TEXT NOT NULL
                )
            ''')
            conn.commit()
        print("Таблица comment_group успешно создана или уже существует.")
    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")


def create_table(group_id):
    conn = create_connection()
    cursor = conn.cursor()
    table_name = f"{group_id}_members"
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute(
        f"""
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT NOT NULL,
            data_id INTEGER NOT NULL,
            liked BOOLEAN NOT NULL DEFAULT FALSE,
            UNIQUE(link)
        )
        """
    )
    conn.commit()
    conn.close()


def insert_link(table_name, link, data_id, conn):
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"INSERT INTO {table_name} (link, data_id, liked) VALUES (?, ?, ?)", (link, data_id, False))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Ссылка уже существует в базе данных: {link}")
        conn.rollback()


def get_last_data_id(table_name, conn):
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(data_id) FROM {table_name}")
    row = cursor.fetchone()
    return row[0] if row[0] is not None else 0


def get_existing_links(table_name, conn):
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT link, liked FROM {table_name} ORDER BY liked ASC, id ASC")
    rows = cursor.fetchall()
    return rows


def update_link_like_status(table_name, link, conn):
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {table_name} SET liked = TRUE WHERE link = ?", (link,))
    conn.commit()


def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_members'")
    tables = cursor.fetchall()
    return [table[0] for table in tables]


def show_tables(message, driver):
    chat_id = message.chat.id
    conn = create_connection()
    try:
        tables = get_tables(conn)
        keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        buttons = [KeyboardButton(text=table) for table in tables]
        keyboard.add(*buttons)
        bot.send_message(
            chat_id, "Выберите таблицу для расстановки лайков:", reply_markup=keyboard)
        bot.register_next_step_handler(
            message, handle_table_selection, driver)  # Передаем driver
    finally:
        conn.close()


def process_next_command(message: Message, driver):
    chat_id = message.chat.id
    user_id = user_data.get(chat_id, {}).get("vk_id")

    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_likes = KeyboardButton(text="Расставить лайки")
    button_comment = KeyboardButton(text="Расставить комментарии")
    keyboard.add(button_likes, button_comment)

    # Отправляем сообщение с клавиатурой
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

    # Регистрируем обработчик для следующего шага после выбора действия
    bot.register_next_step_handler(message, handle_command, driver, user_id)


def handle_command(message: Message, driver, user_id):
    chat_id = message.chat.id
    command = message.text

    if command == "Расставить лайки":
        show_tables(message, driver)  # Передаем driver в show_tables
    elif command == "Расставить комментарии":
        process_comments(message, driver)
    else:
        bot.send_message(
            chat_id, "Неверная команда. Пожалуйста, выберите правильное действие.")
        process_next_command(message, driver)


def request_group_info(message: Message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
    bot.send_message(chat_id, "Введите ID группы VK:")
    bot.register_next_step_handler(message, request_member_count)


def request_member_count(message: Message):
    chat_id = message.chat.id
    group_id = message.text
    user_data[chat_id]['group_id'] = group_id
    bot.send_message(chat_id, "Введите количество участников для сбора:")
    bot.register_next_step_handler(message, request_min_age)


def request_min_age(message: Message):
    chat_id = message.chat.id
    count = int(message.text)
    user_data[chat_id]['count'] = count
    bot.send_message(chat_id, "Введите минимальный возраст:")
    bot.register_next_step_handler(message, request_max_age)


def request_max_age(message: Message):
    chat_id = message.chat.id
    min_age = int(message.text)
    user_data[chat_id]['min_age'] = min_age
    bot.send_message(chat_id, "Введите максимальный возраст:")
    bot.register_next_step_handler(message, request_gender)


def request_gender(message: Message):
    chat_id = message.chat.id
    max_age = int(message.text)
    user_data[chat_id]['max_age'] = max_age
    bot.send_message(
        chat_id, "Введите пол (1 - женский, 2 - мужской, 0 - любой):")
    bot.register_next_step_handler(message, collect_members)


def save_to_db(group_id, members):
    conn = sqlite3.connect("vk_db.db")
    cursor = conn.cursor()
    table_name = f"{group_id}_members"
    for member in members:
        link = f"https://vk.com/{member['domain']}"
        # Используем параметры для вставки данных, включая имя таблицы
        cursor.execute(
            """
            INSERT OR REPLACE INTO {} (link, data_id)
            VALUES (?, ?)
            """.format(table_name),
            (link, member["id"])
        )
    conn.commit()
    conn.close()


# Проверка публичности профиля


def is_profile_public(member):
    # Проверка на заблокированные или удаленные страницы
    if "deactivated" in member:
        return False
    # Проверка на скрытые профили
    if member.get("is_closed", False):
        return False
    # Проверка наличия основных полей
    public_fields = ["bdate", "city", "domain"]
    for field in public_fields:
        if field in member and member[field]:
            return True
    return False


def is_age_in_range(bdate, min_age, max_age):
    if bdate:
        try:
            birth_year = int(bdate.split(".")[-1])
            current_year = time.localtime().tm_year
            age = current_year - birth_year
            return min_age <= age <= max_age
        except ValueError:
            return False
    return False


def get_members(count, min_age, max_age, gender, group_id):
    min_age = int(min_age)
    max_age = int(max_age)
    gender = int(gender)
    offset = 0
    collected_count = 0

    while collected_count < count:
        params = {
            "group_id": group_id,
            "access_token": ACCESS_TOKEN,
            "v": version,
            "sort": "id_asc",
            "count": 1000,
            "fields": "bdate,city,domain,sex,online",
            "offset": offset
        }
        response = requests.get(
            "https://api.vk.com/method/groups.getMembers", params=params
        )
        data = response.json()

        if "response" in data:
            members = data["response"]["items"]

            # Фильтруем только публичные профили, подходящие по возрасту и полу
            public_members = [
                member for member in members
                if is_profile_public(member)
                and member.get("online", 0) == 1
                and (gender == 0 or member.get("sex") == gender)
                and is_age_in_range(member.get("bdate"), min_age, max_age)
            ]

            # Передаем group_id в save_to_db
            save_to_db(group_id, public_members)

            collected_count += len(public_members)

            if len(members) < 1000:
                break
            offset += 1000
        else:
            print(data)
            break

        time.sleep(0.5)


def collect_members(message: Message):
    chat_id = message.chat.id
    gender = int(message.text)
    group_id = user_data[chat_id]['group_id']
    count = user_data[chat_id]['count']
    min_age = int(user_data[chat_id]['min_age'])
    max_age = int(user_data[chat_id]['max_age'])

    create_table(group_id)
    bot.send_message(chat_id, "Сбор участников начат.")
    try:
        get_members(count, min_age, max_age, gender, group_id)
        bot.send_message(chat_id, "Сбор участников завершен.")
    except Exception as e:
        error_message = f"Ошибка при сборе участников: {e}"
        print(error_message)
        bot.send_message(chat_id, error_message)


def handle_table_selection(message: Message, driver):
    chat_id = message.chat.id
    selected_table = message.text

    conn = create_connection()
    try:
        like_posts(selected_table, chat_id, conn, driver)
    except Exception as e:
        error_message = f"Ошибка при расстановке лайков: {e}"
        print(error_message)
        bot.send_message(chat_id, error_message)
    finally:
        conn.close()


# Функция решения капчи
def solve_captcha(driver, bot, chat_id):
    try:
        bot.send_message(chat_id, "Мы столкнулись с капчей!")
        solver = VkCaptchaSolver(logging=True)
        captcha_image = driver.find_element(
            By.XPATH, "//div[@class='vkuiImageBase']//img[@alt='Графический код']")
        captcha_url = captcha_image.get_attribute('src')

        answer, accuracy = solver.solve(
            url=captcha_url, minimum_accuracy=0.4, repeat_count=10)
        print(f"Captcha solved: {answer} with accuracy {accuracy:.4}")

        captcha_input = driver.find_element(
            By.XPATH, "//input[@class='vkuiTypography vkuiInput__el vkuiText vkuiText--sizeY-compact']")
        captcha_input.send_keys(answer)

        submit_button = driver.find_element(
            By.XPATH, "//button[@class='Button-module__root--enpNU vkuiButton vkuiButton--size-l vkuiButton--mode-primary vkuiButton--appearance-accent vkuiButton--align-center vkuiButton--stretched vkuiTappable vkuiInternalTappable vkuiTappable--hasHover vkui-focus-visible']")
        submit_button.click()

        bot.send_message(chat_id, "Я смог её решить, работаем дальше!")
    except Exception as e:
        print(f"Error solving captcha: {e}")
        bot.send_message(chat_id, f"Ошибка при решении капчи: {e}")


# Функий расстановки лайков на пост
def like_posts(selected_table, chat_id, conn, driver):
    try:
        existing_links = get_existing_links(selected_table, conn)

        try:
            bot.send_message(chat_id, "Начинаем расстановку лайков на посты")

            total_likes = 0
            start_time = datetime.now()
            likes_in_session = 0
            last_pause_time = start_time

            for link, liked in existing_links:
                if liked:
                    continue

                while True:  # Добавляем цикл для повторных попыток после решения капчи
                    try:
                        current_time = datetime.now()

                        # Проверка на лимит лайков в сессии
                        if likes_in_session >= 500 and (current_time - start_time).seconds < 12 * 3600:
                            next_session_start = start_time + \
                                timedelta(hours=12)
                            sleep_time = (next_session_start -
                                          current_time).seconds
                            print(
                                f"Лимит лайков достигнут. Спим {sleep_time} секунд до начала новой сессии.")
                            bot.send_message(
                                chat_id, f"Лимит лайков достигнут. Спим {sleep_time} секунд до начала новой сессии.")
                            time.sleep(sleep_time)
                            start_time = datetime.now()
                            likes_in_session = 0
                            last_pause_time = start_time

                        driver.get(link)
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class, '_post_content')]")))

                        post_contents = driver.find_elements(
                            By.XPATH, "//div[contains(@class, '_post_content')]")

                        if not post_contents:
                            bot.send_message(
                                chat_id, f"Не удалось найти посты на странице: {link}")
                            break  # Выход из цикла и переход к следующей ссылке

                        liked_any_post = False
                        for post_content in post_contents:
                            try:
                                like_icon = post_content.find_element(
                                    By.XPATH, ".//span[contains(@class, '_like_button_icon')]//div[contains(@class, 'PostButtonReactions__icon')]")
                                like_icon_class = like_icon.get_attribute(
                                    "class")
                                print(f"Класс иконки лайка: {like_icon_class}")

                                if "PostButtonReactions__icon--custom" in like_icon_class or "PostButtonReactions__icon--filled" in like_icon_class:
                                    print(
                                        "Лайк уже поставлен на этом посте, пропускаем.")
                                    continue

                                # Дополнительные проверки состояния кнопки
                                if not like_icon.is_displayed() or not like_icon.is_enabled():
                                    print(
                                        "Иконка лайка не доступна для клика, пропускаем.")
                                    continue

                                # Попытка кликнуть через JavaScript
                                driver.execute_script(
                                    "arguments[0].click();", like_icon)
                                liked_any_post = True
                                total_likes += 1
                                likes_in_session += 1
                                bot.send_message(
                                    chat_id, f"Лайк поставлен! Всего лайков: {total_likes}")
                                time.sleep(random.randint(5, 15))

                            except Exception as e:
                                print(
                                    f"Ошибка при попытке поставить лайк на посте: {e}")

                        if liked_any_post:
                            update_link_like_status(selected_table, link, conn)
                            bot.send_message(
                                chat_id, f"Лайки поставлены на посты на странице: {link}")
                        else:
                            bot.send_message(
                                chat_id, f"Лайки уже были поставлены ранее на странице: {link}")
                        break  # Выход из цикла и переход к следующей ссылке

                    except Exception as e:
                        if "captcha" in str(e).lower():
                            solve_captcha(driver, bot, chat_id)
                        else:
                            print(f"Ошибка при обработке страницы {link}: {e}")
                            break  # Выход из цикла и переход к следующей ссылке

            bot.send_message(
                chat_id, f"Расстановка лайков завершена. Всего поставлено лайков: {total_likes}")

        except Exception as e:
            error_message = f"Произошла ошибка при расстановке лайков: {e}\n{traceback.format_exc()}"
            print(error_message)
            bot.send_message(chat_id, error_message)

        finally:
            driver.quit()

    except Exception as e:
        error_message = f"Ошибка при получении ссылок из базы данных: {e}"
        print(error_message)
        bot.send_message(chat_id, error_message)


# Основная функция входа на страницуы
def vk_login(
    login, vk_id, chat_id, bot, driver_path=DRIVER_PATH, binary_location=BINARY_LOCATION
):
    # Настройки для Yandex Browser
    options = Options()
    options.binary_location = binary_location
    # options.add_argument("--headless")  # Безголовый режим в случае работы на маке комментим обе эти строчки
    # options.add_argument("--disable-gpu")  # Отключить GPU в случае работы на маке комментим обе эти строчки
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Добавление User-Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options.add_argument(f'user-agent={user_agent}')

    # Создаем экземпляр веб-драйвера с использованием Service
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Загрузка страницы ВКонтакте
        driver.get(f"https://vk.com/{vk_id}/")
        time.sleep(5)  # Пауза для полной загрузки страницы

        # Ожидание, пока кнопка входа станет видимой
        wait = WebDriverWait(driver, 15)
        login_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//button[@class='quick_login_button flat_button button_wide' and text()='Войти']",
                )
            )
        )

        # Клик по кнопке входа через JavaScript
        driver.execute_script("arguments[0].click();", login_button)

        print("Форма для ввода логина и пароля появилась")

        # Найдем поле ввода "телефон или почта" и введем логин
        login_field = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[name='login']"))
        )
        login_field.send_keys(login)

        # Найдем кнопку "Войти" и кликнем по ней
        try:
            submit_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//span[@class='FlatButton__content' and text()='Войти']",
                    )
                )
            )
            submit_button.click()
        except Exception as e:
            print(f"Не удалось найти кнопку Войти после ввода логина: {e}")
            driver.quit()
            return None

        print(f"login {login} input")
        time.sleep(10)  # Пауза после клика, чтобы страница успела обновиться

        # Проверка на необходимость ввода кода
        try:
            otp_title = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[@data-test-id='otp-title']/span")
                )
            )
            if otp_title:
                otp_text = otp_title.text
                bot.send_message(chat_id, f"{otp_text}")
                return driver
        except Exception as e:
            print(f"Не требуется вводить код подтверждения: {e}")
            bot.send_message(
                chat_id,
                "Не требуется вводить код подтверждения. Проверяем необходимость ввода Пароля",
            )
            # Переходим сразу к проверке необходимости ввода пароля
            check_password_field(driver, chat_id, bot)
            return driver

    except Exception as e:
        print(f"Ошибка: {e}")
        driver.quit()

    return None


def check_password_field(driver, chat_id, bot):
    wait = WebDriverWait(driver, 10)
    try:
        # Проверка на необходимость ввода пароля
        password_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='password']"))
        )
        if password_element:
            bot.send_message(chat_id, "Введите ваш пароль ВКонтакте:")
            bot.register_next_step_handler(
                bot.last_message, process_password_step, driver
            )
    except TimeoutException:
        print("Поле для ввода пароля не найдено, переходим к разделу 'Друзья'")
        process_next_command(driver, chat_id, bot)


def enter_password(driver, password):
    wait = WebDriverWait(driver, 10)
    success = True

    # Найти элемент "Пароль" и очистить его
    try:
        password_element = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[name='password']"))
        )
        password_element.clear()  # Очистка поля ввода пароля
        password_element.send_keys(password)  # Ввод нового пароля
        print("Введен пароль")
    except Exception as e:
        print(f"Ошибка при вводе пароля: {e}")
        success = False

    # Нажатие на кнопку "Продолжить"
    try:
        continue_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//span[@class='vkuiButton__in']//span[text()='Продолжить']")
            )
        )
        continue_button.click()
        print("Кликнули на кнопку 'Продолжить'")
    except Exception as e:
        print(f"Ошибка при нажатии кнопки 'Продолжить': {e}")
        success = False

    return success


def process_vk_id_step(message: Message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Ожидайте загрузки данных...")
    # Примерное значение, с которым продолжаем выполнение
    user_data[chat_id]["vk_id"] = 'feed'

    login = message.text  # Получаем логин от пользователя
    user_data[chat_id]["login"] = login  # Сохраняем логин в user_data

    vk_id = user_data[chat_id]["vk_id"]

    # Вызов функции vk_login и обработка двухфакторной аутентификации
    driver = vk_login(login, vk_id, chat_id, bot)
    if driver:
        bot.register_next_step_handler(
            message, lambda message: process_otp_step(message, driver)
        )


def process_otp_step(message: Message, driver):
    chat_id = message.chat.id
    otp_code = message.text

    wait = WebDriverWait(driver, 10)
    otp_field = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='otp-cell']"))
    )
    otp_field.send_keys(otp_code)

    try:
        # Ждем некоторое время, чтобы система успела проверить код
        time.sleep(2)

        # Проверка на наличие ошибки в поле ввода кода
        error_message = driver.find_elements(
            By.CSS_SELECTOR, ".vkc__CellInput__error")
        if error_message:
            bot.send_message(
                chat_id, "Вы ввели неверный код. Пожалуйста, попробуйте еще раз.")
            msg = bot.send_message(
                chat_id, "Введите код для двухфакторной аутентификации:")
            bot.register_next_step_handler(msg, process_otp_step, driver)
            return

        # Ждем появления поля ввода пароля
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='password']"))
        )
        # Запрос пароля после ввода кода
        msg = bot.send_message(chat_id, "Введите ваш пароль ВКонтакте:")
        bot.register_next_step_handler(msg, process_password_step, driver)
    except TimeoutException:
        print("Поле для ввода пароля не найдено, переходим к разделу 'Друзья'")
        process_next_command(message, driver)


def process_password_step(message: Message, driver):
    chat_id = message.chat.id
    password = message.text

    # Вызов функции для ввода пароля и нажатия кнопки "Продолжить"
    if enter_password(driver, password):
        time.sleep(2)
        # Проверка на наличие ошибки при вводе пароля
        error_message = driver.find_elements(
            By.CSS_SELECTOR, ".vkc__TextField__errorMessage")
        if error_message:
            bot.send_message(
                chat_id, "Вы ввели неверный пароль. Пожалуйста, попробуйте еще раз.")
            msg = bot.send_message(chat_id, "Введите ваш пароль ВКонтакте:")
            bot.register_next_step_handler(msg, process_password_step, driver)
        else:
            # Переход к выбору дальнейшего действия
            process_next_command(message, driver)
    else:
        bot.send_message(
            chat_id, "Произошла ошибка при попытке ввода пароля. Пожалуйста, попробуйте снова.")
        msg = bot.send_message(chat_id, "Введите ваш пароль ВКонтакте:")
        bot.register_next_step_handler(msg, process_password_step, driver)


# Установка времени ожидания для всех запросов к API Telegram
bot.timeout = 60  # Увеличиваем время ожидания до 60 секунд

# Функция для безопасного отправления сообщений с повторной попыткой


def safe_send_message(chat_id, text):
    try:
        bot.send_message(chat_id, text)
    except requests.exceptions.ReadTimeout:
        print("ReadTimeout error occurred. Retrying...")
        time.sleep(5)  # Ожидание перед повторной попыткой
        bot.send_message(chat_id, text)


# Запуск бота
bot.polling()

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
import time
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from selenium.common.exceptions import TimeoutException
import json
import re
import random
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOCKEN")
DRIVER_PATH = os.getenv("DRIVER_PATH")
BINARY_LOCATION = os.getenv("BINARY_LOCATION")

user_data = {}

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [KeyboardButton(text="Регистрация")]
main_keyboard.add(*buttons)


def enter_friends(driver, chat_id, user_id, command, group_id=None):
    try:
        filename = f"friends_{user_id}.json"

        # Загружаем уже сохраненные ссылки, если файл существует
        existing_links = set()
        if os.path.exists(filename):
            with open(filename, "r") as f:
                for line in f:
                    existing_links.update(json.loads(line))

        if command == "/likefriends":
            friends_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/friends']"))
            )
            friends_link.click()
            print("Переход в раздел 'Друзья'")

            friends_count_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "span.ui_tab_count_new")
                )
            )
            friends_count_text = friends_count_element.text
            friends_count = int(re.sub(r"\D", "", friends_count_text))
            print("Найдено друзей:", friends_count)
            bot.send_message(chat_id, f"Найдено друзей: {friends_count}")

            scroll_counter = 0
            while True:
                friends_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".friends_field_title a")
                    )
                )

                new_links = []
                for friend_element in friends_elements:
                    friend_link = friend_element.get_attribute("href")
                    if friend_link not in existing_links:
                        new_links.append(friend_link)
                        existing_links.add(friend_link)

                if new_links:
                    with open(filename, "a") as f:
                        json.dump(new_links, f)
                        f.write("\n")
                else:
                    break

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                scroll_counter += 1
                if scroll_counter >= 3:
                    scroll_counter = 0
                    time.sleep(1)

            bot.send_message(chat_id, "Ссылки друзей собраны и сохранены.")
            like_posts(user_id, filename, driver, chat_id)

        elif command == "/likegroup":
            while True:
                try:
                    group_link = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "//div[@class='header_top clear_fix']//span[text()='Подписчики']",
                            )
                        )
                    )
                    group_link.click()
                    print("Переход в раздел 'Подписчики'")
                    break
                except Exception as e:
                    driver.execute_script("window.scrollBy(0, 200);")
                    time.sleep(0.5)
                    print("Прокрутка страницы вниз для поиска элемента 'Подписчики'")

            group_count_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".header_count"))
            )
            group_count_text = group_count_element.text
            group_count = int(re.sub(r"\D", "", group_count_text))
            print(f"Найдено подписчиков: {group_count}")
            bot.send_message(chat_id, f"Найдено подписчиков: {group_count}")

            while True:
                group_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".fans_fan_row .fans_fan_name a.fans_fan_lnk")
                    )
                )

                new_links = []
                for group_element in group_elements:
                    group_link = group_element.getAttribute("href")
                    if group_link not in existing_links:
                        new_links.append(group_link)
                        existing_links.add(group_link)
                        print(f"Добавлена ссылка {group_link}")

                if new_links:
                    with open(filename, "a") as f:
                        json.dump(new_links, f)
                        f.write("\n")
                else:
                    break

                try:
                    scrollable_element = driver.find_element(
                        By.CSS_SELECTOR, "._scroll_node.fans_box"
                    )
                    load_more_button = driver.find_element(
                        By.CSS_SELECTOR,
                        "button.flat_button.ui_load_more_btn#fans_more_linkmembers",
                    )
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", load_more_button
                    )
                    time.sleep(1)
                except Exception as e:
                    print(f"Ошибка при прокрутке: {e}")
                    break

            bot.send_message(chat_id, "Ссылки группы собраны и сохранены.")
            like_posts(user_id, filename, driver, chat_id)

    except Exception as e:
        error_message = f"Произошла ошибка: {e}\n{traceback.format_exc()}"
        print(error_message)
        bot.send_message(chat_id, error_message)


def like_posts(user_id, filename, driver, chat_id):
    try:
        friends_links = []
        with open(filename, "r") as f:
            for line in f:
                friends_links.extend(json.loads(line))
    except FileNotFoundError:
        print(f"Файл {filename} не найден.")
        return

    bot.send_message(chat_id, "Начинаем расстановку лайков на посты друзей")
    total_likes = 0

    for link in friends_links:
        try:
            driver.get(link)
            time.sleep(random.randint(60, 90))

            post_contents = []
            for _ in range(10):
                try:
                    post_contents = driver.find_elements(
                        By.XPATH, "//div[contains(@class, '_post_content')]"
                    )
                    if post_contents:
                        break
                except:
                    driver.execute_script("window.scrollBy(0, 200);")
                    time.sleep(1)

            if not post_contents:
                bot.send_message(chat_id, f"Не удалось найти посты на странице {link}")
                continue

            liked_any_post = False
            for post_content in post_contents:
                try:
                    like_icon = post_content.find_element(
                        By.XPATH,
                        ".//div[contains(@class, 'PostButtonReactions__icon')]",
                    )
                    if "PostButtonReactions__icon--custom" in like_icon.getAttribute(
                        "class"
                    ) or "PostButtonReactions__icon--filled" in like_icon.getAttribute(
                        "class"
                    ):
                        continue

                    like_icon.click()
                    liked_any_post = True
                    total_likes += 1
                    time.sleep(random.randint(30, 60))

                except Exception as e:
                    print(f"Ошибка при попытке поставить лайк на посте: {e}")

            if liked_any_post:
                bot.send_message(
                    chat_id, f"Лайки поставлены на посты на странице {link}"
                )
            else:
                bot.send_message(
                    chat_id, f"Лайки уже были поставлены ранее на странице {link}"
                )

        except Exception as e:
            print(f"Ошибка при обработке страницы {link}: {e}")

    bot.send_message(
        chat_id, f"Расстановка лайков завершена. Всего поставлено лайков: {total_likes}"
    )


# Основной код для запуска драйвера и бота, а также ваши остальные функции


def vk_login(
    login, vk_id, chat_id, bot, driver_path=DRIVER_PATH, binary_location=BINARY_LOCATION
):
    # Настройки для Yandex Browser
    options = Options()
    options.binary_location = binary_location
    options.add_argument("--headless")  # Безголовый режим
    options.add_argument("--disable-gpu")  # Отключить GPU
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Создаем экземпляр веб-драйвера с использованием Service
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Загрузка страницы ВКонтакте
        driver.get(f"https://vk.com/{vk_id}/")

        # Ожидание, пока кнопка входа станет видимой
        wait = WebDriverWait(driver, 10)
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
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='login']"))
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
        except:
            print("Не удалось найти кнопку Войти после ввода логина")
            driver.quit()
            return None

        print(f"login {login} input")
        time.sleep(10)

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
        except:
            print("Не требуется вводить код подтверждения")
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
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
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

    # Найти элемент "Пароль" и ввести пароль
    try:
        password_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']"))
        )
        password_element.send_keys(password)
        print("Введен пароль")
    except Exception as e:
        print(f"Ошибка при вводе пароля: {e}")

    # Нажатие на кнопку "Продолжить"
    try:
        continue_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[@class='vkuiButton__in']//span[text()='Продолжить']")
            )
        )
        continue_button.click()
        print("Кликнули на кнопку 'Продолжить'")
    except Exception as e:
        print(f"Ошибка при нажатии кнопки 'Продолжить': {e}")


bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=["start"])
def bot_start(message: Message):
    bot.send_message(
        message.chat.id,
        "Добрый день вы попали в бот по автолайкингу в VK",
        reply_markup=main_keyboard,
    )


@bot.message_handler(func=lambda message: message.text == "Регистрация")
def auto_like(message: Message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    msg = bot.send_message(chat_id, "Введите ваш логин ВКонтакте:")
    bot.register_next_step_handler(msg, process_login_step)


def process_login_step(message: Message):
    chat_id = message.chat.id
    user_data[chat_id]["login"] = message.text
    msg = bot.send_message(
        chat_id,
        "Введите ваш VK ID или группы где хотите проставить лайки и ожидайте прогрузки данных.",
    )
    bot.register_next_step_handler(msg, process_vk_id_step)


def process_vk_id_step(message: Message):
    chat_id = message.chat.id
    user_data[chat_id]["vk_id"] = message.text

    login = user_data[chat_id]["login"]
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
        # Ждем появления поля ввода пароля
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
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
    enter_password(driver, password)
    time.sleep(10)
    # Переход к выбору дальнейшего действия
    process_next_command(message, driver)


def process_next_command(message: Message, driver):
    chat_id = message.chat.id
    user_id = user_data[chat_id]["vk_id"]

    bot.send_message(
        chat_id, "Вы удачно авторизовались.\nВыберите дальнейшее действие:"
    )
    command = message.text
    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_friends = KeyboardButton(text="Лайкнуть друзей")
    button_group = KeyboardButton(text="Лайкнуть группу")
    keyboard.add(button_friends, button_group)

    # Отправляем сообщение с клавиатурой
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

    if command == "Лайкнуть друзей":
        enter_friends(driver, chat_id, user_id, "/likefriends")
    elif command == "Лайкнуть группу":
        enter_friends(driver, chat_id, user_id, "/likegroup")

    bot.register_next_step_handler_by_chat_id(chat_id, process_next_command, driver)


# Запуск бота
bot.polling()

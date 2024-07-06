
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
from django.shortcuts import render
from .models import Link, Document

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOCKEN")
DRIVER_PATH = os.getenv("DRIVER_PATH")
BINARY_LOCATION = os.getenv("BINARY_LOCATION")

user_data = {}

# Сбор ссылок друзей


def collect_friends_links(user_id, driver):
    try:
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
                if not Link.objects.filter(link=friend_link).exists():
                    new_links.append(friend_link)
                    # Сохраняем ссылку в базу данных
                    Link.objects.create(name="Друзья", link=friend_link)

            if new_links:
                print(f"Добавлены новые ссылки: {new_links}")
            else:
                break

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            scroll_counter += 1
            if scroll_counter >= 3:
                scroll_counter = 0
                time.sleep(1)

        print("Ссылки друзей собраны и сохранены.")
        # like_posts(user_id, driver)  # вызов вашей функции для лайков

    except Exception as e:
        error_message = f"Произошла ошибка: {e}\n{traceback.format_exc()}"
        print(error_message)

# Сбор ссылок участников группы


def collect_group_links(user_id, driver):
    try:
        while True:
            try:
                group_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//div[@class='header_top clear_fix']//span[text()='Подписчики']")
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
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".header_count"))
        )
        group_count_text = group_count_element.text
        group_count = int(re.sub(r"\D", "", group_count_text))
        print(f"Найдено подписчиков: {group_count}")

        while True:
            group_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".fans_fan_row .fans_fan_name a.fans_fan_lnk")
                )
            )

            new_links = []
            for group_element in group_elements:
                group_link = group_element.get_attribute("href")
                if not Link.objects.filter(link=group_link).exists():
                    new_links.append(group_link)
                    # Сохраняем ссылку в базу данных
                    Link.objects.create(name="Подписчики", link=group_link)
                    print(f"Добавлена ссылка {group_link}")

            if new_links:
                print(f"Добавлены новые ссылки: {new_links}")
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

        print("Ссылки группы собраны и сохранены.")
        # like_posts(user_id, driver)  # вызов вашей функции для лайков

    except Exception as e:
        error_message = f"Произошла ошибка: {e}\n{traceback.format_exc()}"
        print(error_message)

# Расстановка лайков


def like_posts(user_id, driver):
    print("Начинаем расстановку лайков на посты друзей")
    total_likes = 0
    log_messages = []

    # Получаем все ссылки из базы данных
    friends_links = Link.objects.values_list('link', flat=True)

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
                log_messages.append(
                    f"Не удалось найти посты на странице {link}")
                continue

            liked_any_post = False
            for post_content in post_contents:
                try:
                    like_icon = post_content.find_element(
                        By.XPATH,
                        ".//div[contains(@class, 'PostButtonReactions__icon')]",
                    )
                    if "PostButtonReactions__icon--custom" in like_icon.get_attribute(
                        "class"
                    ) or "PostButtonReactions__icon--filled" in like_icon.get_attribute(
                        "class"
                    ):
                        continue

                    like_icon.click()
                    liked_any_post = True
                    total_likes += 1
                    time.sleep(random.randint(30, 60))

                except Exception as e:
                    log_messages.append(
                        f"Ошибка при попытке поставить лайк на посте: {e}")

            if liked_any_post:
                log_messages.append(
                    f"Лайки поставлены на посты на странице {link}")
            else:
                log_messages.append(
                    f"Лайки уже были поставлены ранее на странице {link}")

        except Exception as e:
            log_messages.append(f"Ошибка при обработке страницы {link}: {e}")

    log_messages.append(
        f"Расстановка лайков завершена. Всего поставлено лайков: {total_likes}")
    for message in log_messages:
        print(message)

# Авторизация


def vk_login(login, vk_id, driver_path=DRIVER_PATH, binary_location=BINARY_LOCATION):
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
                print(f"Требуется ввод кода: {otp_text}")
                return {"driver": driver, "otp_required": True}
        except:
            print("Не требуется вводить код подтверждения")
            print("Проверяем необходимость ввода пароля")
            check_password_field(driver)
            return {"driver": driver, "otp_required": False}

    except Exception as e:
        print(f"Ошибка: {e}")
        driver.quit()

    return None

# Проверка необходимости ввода пароля


def check_password_field(driver):
    wait = WebDriverWait(driver, 10)
    try:
        # Проверка на необходимость ввода пароля
        password_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='password']"))
        )
        if password_element:
            print("Требуется ввод пароля")
            return {"password_required": True}
    except:
        print("Поле для ввода пароля не найдено, переходим к разделу 'Друзья'")
        return {"password_required": False}

# Функция ввода пароля


def enter_password(driver, password):
    wait = WebDriverWait(driver, 10)

    # Найти элемент "Пароль" и ввести пароль
    try:
        password_element = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[name='password']"))
        )
        password_element.send_keys(password)
        print("Введен пароль")
    except Exception as e:
        print(f"Ошибка при вводе пароля: {e}")

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

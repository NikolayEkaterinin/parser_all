import os
import sqlite3
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
DRIVER_PATH = os.getenv("DRIVER_PATH")
BINARY_LOCATION = os.getenv("BINARY_LOCATION")


def yandex_maps():
    options = Options()
    options.binary_location = BINARY_LOCATION
    # options.add_argument("--headless")  # Безголовый режим
    # options.add_argument("--disable-gpu")  # Отключить GPU
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Добавление User-Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options.add_argument(f'user-agent={user_agent}')

    # Создаем экземпляр веб-драйвера с использованием Service
    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get('https://yandex.ru/maps/')
        time.sleep(10)
    except:
        print('Загрузка Яндекс Карт не удалась')


yandex_maps()

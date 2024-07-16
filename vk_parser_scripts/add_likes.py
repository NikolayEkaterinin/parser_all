import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# Загрузка переменных окружения
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
GROUP_SCREEN_NAME = os.getenv("GROUP_SCREEN_NAME")  # Короткий адрес группы
version = "5.202"  # Обновленная версия API

# Запрещенные слова или фразы
forbidden_words = {
    "Война",
    "Украина",
    "Путин",
    "бомба",
    "Зелинский",
    "Слава Украине",
    "Слава России",
}

# Функция для получения числового идентификатора группы


def get_group_id(screen_name):
    url = "https://api.vk.com/method/groups.getById"
    params = {
        "group_id": screen_name,
        "access_token": ACCESS_TOKEN,
        "v": version,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"Ответ API: {data}")  # Выводим полный ответ API для диагностики
        if "response" in data and "groups" in data["response"] and data["response"]["groups"]:
            # Получаем id первой группы из списка
            return data["response"]["groups"][0]["id"]
        elif "error" in data:
            error_code = data["error"]["error_code"]
            error_msg = data["error"]["error_msg"]
            print(f"Ошибка VK API {error_code}: {error_msg}")
        else:
            print("Неизвестная ошибка VK API")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка HTTP-запроса: {e}")

    return None


# Функция для установки лайка


def add_like(owner_id, post_id):
    url = "https://api.vk.com/method/wall.get"
    params = {
        "type": "post",
        "owner_id": -owner_id,  # Отрицательное значение для групп
        "item_id": post_id,
        "access_token": ACCESS_TOKEN,
        "v": version,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Проверяем статус ответа
        data = response.json()
        if "response" in data:
            return data["response"]
        elif "error" in data:
            error_code = data["error"]["error_code"]
            error_msg = data["error"]["error_msg"]
            print(f"Ошибка VK API {error_code}: {error_msg}")
        else:
            print("Неизвестная ошибка VK API")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка HTTP-запроса: {e}")

    return None

# Функция для получения постов группы


def get_group_posts(group_id, count=10):
    url = "https://api.vk.com/method/wall.get"
    params = {
        "owner_id": -group_id,  # Отрицательное значение для групп
        "count": count,  # Количество постов для получения
        "extended": 0,  # Не получаем расширенную информацию о посте
        "access_token": ACCESS_TOKEN,
        "v": version,
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "response" in data and data["response"]["items"]:
        return data["response"]["items"]
    return []

# Функция для проверки текста на наличие запрещенных слов


def validate_text(text):
    text_lower = text.lower()
    for word in forbidden_words:
        if word.lower() in text_lower:
            print(f"В тексте обнаружено запрещенное слово: {word}")
            return False
    return True


# Получение числового идентификатора группы
GROUP_ID = get_group_id(GROUP_SCREEN_NAME)
if GROUP_ID is None:
    print("Не удалось получить идентификатор группы.")
    exit()

# Получаем посты группы
posts = get_group_posts(GROUP_ID, count=10)

# Лайкаем посты группы без ограничений
likes_count = 0

for post in posts:
    post_id = post["id"]
    post_text = post.get("text", "")  # Текст поста (если есть)
    if validate_text(post_text):
        result = add_like(GROUP_ID, post_id)
        print(f"Результат для поста {post_id}: {result}")
        likes_count += 1
        time.sleep(1)
    else:
        print(f"Пропуск лайка для поста {post_id} из-за запрещенных слов")

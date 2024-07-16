import os
import requests
import sqlite3
import time
from dotenv import load_dotenv

load_dotenv()

# Замените на ваш access token
ACCESS_TOKEN = os.getenv("SERVES_KEY")
group_id = "yarchat"
version = "5.199"

# Функция для создания таблицы, если ее нет


def create_table():
    conn = sqlite3.connect("vk_db.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS f'{group_id}_members' (
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

# Функция для сохранения данных в базу данных


def save_to_db(members):
    conn = sqlite3.connect("vk_db.db")
    cursor = conn.cursor()
    for member in members:
        link = f"https://vk.com/{member['domain']}"
        cursor.execute(
            """
            INSERT OR REPLACE INTO f'{group_id}_members' (link, data_id)
            VALUES (?, ?)
        """,
            (
                link,
                member["id"],
            ),
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

# Проверка возраста профиля


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

# Получение и сохранение всех участников группы


def get_members(count, min_age, max_age, gender):
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

            save_to_db(public_members)

            collected_count += len(public_members)

            if len(members) < 1000:
                break
            offset += 1000
        else:
            print(data)
            break

        time.sleep(0.5)


# Основной блок
if __name__ == "__main__":
    create_table()
    # Задайте параметры: количество собранных подписчиков, минимальный и максимальный возраст, пол (1 - женский, 2 - мужской, 0 - любой)
    target_count = 200
    min_age = 25
    max_age = 30
    gender = 1

    get_members(target_count, min_age, max_age, gender)

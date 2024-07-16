"""
q — поисковый запрос (например, имя или фамилия).
sort — сортировка (0 — по популярности, 1 — по дате регистрации).
count — количество возвращаемых пользователей (максимум 1000).
offset — смещение для получения следующей страницы результатов.
city — идентификатор города.
country — идентификатор страны.
hometown — название родного города.
university_country — идентификатор страны, в которой был окончен университет.
university — идентификатор университета.
university_year — год окончания университета.
university_faculty — идентификатор факультета.
university_chair — идентификатор кафедры.
sex — пол (1 — женский, 2 — мужской).
status — семейное положение.
age_from — минимальный возраст.
age_to — максимальный возраст.
birth_day — день рождения.
birth_month — месяц рождения.
birth_year — год рождения.
online — искать только пользователей в сети (1 — да).
has_photo — искать только пользователей с фотографией (1 — да).
school_country — идентификатор страны, в которой была окончена школа.
school_city — идентификатор города, в котором была окончена школа.
school_class — номер класса, в котором учился пользователь.
school — идентификатор школы.(вводится идентификатор, если навести на ссылку школы, можно увидеть)
school_year — год окончания школы.
religion — религиозные взгляды.
interests — интересы.
company — название компании, в которой работает пользователь(Вводится название)
position — должность, которую занимает пользователь.
group_id — идентификатор группы, чтобы искать только участников этой группы.
from_list — откуда пришли пользователи.
"""


import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Замените на ваш access token
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Задайте параметры поиска
params = {
    "q": "",
    "sort": 0,
    "count": 1000,
    "offset": 0,
    "city": "",
    "country": "",
    "hometown": "",
    "university_country": "",
    "university": "",
    "university_year": "",
    "university_faculty": "",
    "university_chair": "",
    "sex": "",
    "status": "",
    "age_from": "",
    "age_to": "",
    "birth_day": "",
    "birth_month": "",
    "birth_year": "",
    "online": "",
    "has_photo": "",
    "school_country": "",
    "school_city": "",
    "school_class": "",
    "school": "",
    "school_year": "",
    "religion": "",
    "interests": "",
    "company": "Ярославский Медицинский Колледж",
    "position": "",
    "group_id": "",
    "from_list": "",
    "fields": "bdate,city,domain,education,schools,military,career",
    "access_token": ACCESS_TOKEN,
    "v": "5.131",
}

# Удаление пустых параметров
params = {k: v for k, v in params.items() if v}

# Запрос к VK API
url = "https://api.vk.com/method/users.search"
response = requests.get(url, params=params)
data = response.json()

if "response" in data:
    users = data["response"]["items"]
    user_data = []
    for user in users:
        user_info = {
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "bdate": user.get("bdate", ""),
            "profile_url": f"https://vk.com/{user['domain']}",
            "education": user.get("education", {}),
            "schools": user.get("schools", []),
            "military": user.get("military", []),
            "career": user.get("career", []),
        }
        user_data.append(user_info)

    # Сохранение данных в JSON файл
    with open("share_users_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)
else:
    print(f"Ошибка в ответе от API: {data}")

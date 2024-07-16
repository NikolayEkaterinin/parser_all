import os

import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Замените на ваш access token
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
# Координаты центра локации (широта и долгота)
latitude = 57.58924
longitude = 39.85666

# Радиус поиска в километрах
radius = 1

# Запрос к VK API
url = f"https://api.vk.com/method/users.search?sort=0&count=1000&fields=bdate,city,domain,education,schools,military,career&lat={latitude}&long={longitude}&radius={radius}&access_token={ACCESS_TOKEN}&v=5.131"

response = requests.get(url)
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
    with open("GPS_users_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)
else:
    print(data)

import requests
import sqlite3

# Функция для получения данных по API и сохранения в базу данных


def fetch_and_save_data(region=None):
    base_url = 'https://egrul.itsoft.ru/'

    # Определяем список ссылок в зависимости от указанного региона или всех данных
    if region:
        urls = [
            f'{base_url}{region}.json',
            f'{base_url}{region}.xml',
            f'{base_url}{region}'
        ]
    else:
        urls = [
            f'{base_url}org.json',
            f'{base_url}org.xml',
            f'{base_url}org'
        ]

    # Используем SQLite для хранения данных
    conn = sqlite3.connect('egrul.db')
    cursor = conn.cursor()

    # Создаем таблицу для организаций и ИП, если она не существует
    cursor.execute('''CREATE TABLE IF NOT EXISTS organizations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ogrn TEXT,
                        inn TEXT,
                        full_name TEXT,
                        region TEXT
                    )''')

    # Обработка каждой ссылки
    for url in urls:
        try:
            response = requests.get(url, headers={'Accept-encoding': 'gzip'})
            response.raise_for_status()  # Проверяем на ошибки HTTP

            if response.status_code == 200:
                data = response.json()  # предполагается, что данные приходят в формате JSON

                # Вставляем данные в базу
                for item in data:
                    if 'ogrn' in item and 'inn' in item and 'full_name' in item:
                        cursor.execute('''INSERT INTO organizations (ogrn, inn, full_name, region)
                                          VALUES (?, ?, ?, ?)''',
                                       (item['ogrn'], item['inn'], item['full_name'], region))
                conn.commit()

        except requests.exceptions.RequestException as e:
            print(f'Ошибка при обработке {url}: {e}')

    conn.close()
    print('Данные успешно собраны и сохранены в базу данных.')


# Пример вызова функции для сбора всех данных
fetch_and_save_data()

# Пример вызова функции для сбора данных по конкретному региону (например, Москва)
# fetch_and_save_data('moscow')

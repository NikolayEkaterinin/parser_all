import requests
from bs4 import BeautifulSoup
import re


def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на успешный статус запроса
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении HTML-кода: {e}")
        return None


def check_for_sql_injection(html):
    # Примеры паттернов, которые могут указывать на возможные SQL-инъекции
    sql_patterns = [
        r"\bSELECT\b",
        r"\bUNION\b",
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"--",
        r";--",
        r"' OR '1'='1",
        r"\" OR \"1\"=\"1",
        r"\('1'='1",
        r"\(\"1\"=\"1",
    ]

    for pattern in sql_patterns:
        try:
            if re.search(pattern, html, re.IGNORECASE):
                print(f"Найден возможный SQL-инъекционный паттерн: {pattern}")
                return True
        except re.error as e:
            print(f"Ошибка в регулярном выражении {pattern}: {e}")

    print("Уязвимости SQL-инъекции не найдены.")
    return False


def main(url):
    html = fetch_html(url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        # Извлекаем текстовые данные для проверки на уязвимости
        text = soup.get_text()
        check_for_sql_injection(text)


if __name__ == "__main__":
    # Замените 'http://example.com' на URL, который вы хотите проверить
    url = "https://otrs.ivoin.ru/"
    main(url)

from rasa.nlu.model import Interpreter

# Укажите путь к модели Rasa NLU
model_path = "/path/to/your/rasa/model"

# Загрузка модели
interpreter = Interpreter.load(model_path)


def get_rasa_response(user_message):
    # Анализ текста с помощью модели Rasa
    result = interpreter.parse(user_message)

    # Возвращаем текст ответа
    if 'text' in result:
        return result['text']['response']
    else:
        return "Не удалось получить ответ от Rasa."


# Пример использования
user_message = "Hello, how are you?"
response = get_rasa_response(user_message)
print(f"Ответ на '{user_message}': {response}")

user_message = "What is the weather like today?"
response = get_rasa_response(user_message)
print(f"Ответ на '{user_message}': {response}")

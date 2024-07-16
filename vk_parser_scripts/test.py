from PIL import Image
import cv2
import numpy as np


def count_empty_cells(image_path):
    # Открываем изображение при помощи Pillow
    image = Image.open(image_path)

    # Преобразуем изображение в массив NumPy
    image_array = np.array(image)

    # Преобразуем изображение в оттенки серого
    gray_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)

    # Бинаризуем изображение (делаем черно-белым) с порогом 200
    _, binary_image = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY)

    # Находим контуры на изображении
    contours, _ = cv2.findContours(
        binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Подсчитываем количество контуров (пустых ячеек)
    empty_cells_count = len(contours)

    return empty_cells_count


# Пример использования
image_path = "IMG_3392.jpeg"
empty_cells = count_empty_cells(image_path)
print(f"Количество пустых ячеек на изображении: {empty_cells}")

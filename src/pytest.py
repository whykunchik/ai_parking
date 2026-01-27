import cv2
import pytesseract as pytess
from imutils import contours
import os

# Проверка существования файла
tesseract_path = r'C:\tess\tesseract.exe'
if not os.path.exists(tesseract_path):
    print(f"ОШИБКА: Файл не найден: {tesseract_path}")
    print("Tesseract не установлен или установлен в другом месте")
    
    # Проверим возможные пути
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME')),
        r'D:\Tesseract-OCR\tesseract.exe',
        r'C:\tesseract\tesseract.exe'
    ]
    
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            tesseract_path = path
            print(f"Найден Tesseract по пути: {path}")
            found = True
            break
    
    if not found:
        print("Tesseract не найден! Установите его:")
        print("1. Скачайте с: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Установите, запомните путь установки")
        print("3. Обновите путь в коде")
        exit(1)

pytess.pytesseract.tesseract_cmd = tesseract_path
print(f"Используется Tesseract: {tesseract_path}")

# Проверка работы Tesseract
try:
    version = pytess.get_tesseract_version()
    print(f"Tesseract версия: {version}")
except:
    print("Не удалось получить версию Tesseract")

# Дальше ваш код...
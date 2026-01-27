import cv2
import pytesseract as pytess
from imutils import contours
import numpy as np
import os

# ===== НАСТРОЙКА TESSERACT =====
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytess.pytesseract.tesseract_cmd = tesseract_path
    print(f"✓ Tesseract найден: {tesseract_path}")
else:
    print("✗ Tesseract не найден!")
    exit(1)

# ===== ФУНКЦИИ ПРЕДОБРАБОТКИ =====
def preprocess_image(image):
    """Улучшает качество изображения для распознавания"""
    # Преобразуем в серый
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Убираем шум с помощью медианного фильтра
    gray = cv2.medianBlur(gray, 3)
    
    # Улучшаем контраст с помощью CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Убираем мелкие шумы морфологическими операциями
    kernel = np.ones((1,1), np.uint8)
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    
    return gray

def find_license_plate_contours(image, gray):
    """Находит контуры, похожие на номерные знаки"""
    # Адаптивное пороговое преобразование (лучше чем глобальное)
    thresh = cv2.adaptiveThreshold(gray, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Улучшаем контуры
    kernel = np.ones((3,3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.dilate(thresh, kernel, iterations=1)
    
    # Находим контуры
    cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    
    # Фильтруем контуры по форме и размеру
    license_plates = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 500 or area > 50000:  # игнорируем слишком маленькие и большие
            continue
            
        # Получаем bounding box
        x, y, w, h = cv2.boundingRect(c)
        
        # Пропорции номерного знака (ширина > высоты)
        aspect_ratio = w / float(h)
        
        # Стандартные пропорции номерных знаков ~ 2:1 до 4:1
        if 1.5 < aspect_ratio < 6.0:
            # Вычисляем solidity (отношение площади контура к площади bounding box)
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            if hull_area > 0:
                solidity = area / float(hull_area)
                if solidity > 0.3:  # должен быть достаточно плотным
                    license_plates.append((c, x, y, w, h))
    
    return license_plates, thresh

def process_license_plate(roi):
    """Обрабатывает найденный номерной знак для лучшего распознавания"""
    # Преобразуем в серый
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Увеличиваем контраст
    gray_roi = cv2.equalizeHist(gray_roi)
    
    # Медианный фильтр для удаления шума
    gray_roi = cv2.medianBlur(gray_roi, 3)
    
    # Адаптивное пороговое преобразование
    thresh_roi = cv2.adaptiveThreshold(gray_roi, 255,
                                      cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
    
    # Убираем мелкие шумы
    kernel = np.ones((2,2), np.uint8)
    thresh_roi = cv2.morphologyEx(thresh_roi, cv2.MORPH_CLOSE, kernel)
    thresh_roi = cv2.erode(thresh_roi, kernel, iterations=1)
    
    # Увеличиваем изображение для лучшего распознавания
    scale_factor = 2
    new_width = thresh_roi.shape[1] * scale_factor
    new_height = thresh_roi.shape[0] * scale_factor
    thresh_roi = cv2.resize(thresh_roi, (new_width, new_height), 
                           interpolation=cv2.INTER_CUBIC)
    
    return thresh_roi

def clean_text(text):
    """Очищает распознанный текст от мусора"""
    # Убираем лишние пробелы и переводы строк
    text = ' '.join(text.split())
    
    # Убираем специальные символы, оставляем только буквы, цифры и пробелы
    import re
    text = re.sub(r'[^A-ZА-Я0-9\s]', '', text.upper())
    
    # Убираем одиночные буквы и цифры (скорее всего ошибки)
    words = text.split()
    cleaned_words = []
    for word in words:
        if len(word) >= 2:  # минимум 2 символа
            # Проверяем, что это похоже на номер
            if any(c.isdigit() for c in word) and any(c.isalpha() for c in word):
                cleaned_words.append(word)
    
    return ' '.join(cleaned_words)

# ===== ОСНОВНОЙ КОД =====
image = cv2.imread("images/image99.jpg")
if image is None:
    print("Ошибка загрузки изображения!")
    exit()

print("Обработка изображения...")

# 1. ПРЕДОБРАБОТКА ВСЕГО ИЗОБРАЖЕНИЯ
gray = preprocess_image(image)

# 2. ПОИСК НОМЕРНЫХ ЗНАКОВ
license_plates, thresh = find_license_plate_contours(image, gray)

print(f"Найдено {len(license_plates)} возможных номерных знаков")

# 3. РАСПОЗНАВАНИЕ ТЕКСТА
results = []

for i, (c, x, y, w, h) in enumerate(license_plates):
    print(f"\nОбработка номерного знака {i+1}:")
    
    # Вырезаем область
    roi = image[y:y+h, x:x+w]
    
    # Обрабатываем номерной знак
    processed_roi = process_license_plate(roi)
    
    # Настройки Tesseract для номерных знаков
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABEKMHOPCTYXАВЕКМНОРСТУХ0123456789 -l eng+rus'
    # Параметр psm 7: обрабатывать изображение как одну текстовую строку
    # whitelist: только разрешенные символы (русские и английские буквы + цифры)
    
    try:
        # Распознаем текст
        result = pytess.image_to_string(processed_roi, config=custom_config)
        result = clean_text(result)
        
        if result:
            print(f"  Сырой текст: '{result}'")
            
            # Дополнительная проверка на валидность номера
            # Российские номера: буква-3цифры-2буквы или подобные форматы
            if (len(result) >= 6 and 
                any(c.isalpha() for c in result) and 
                any(c.isdigit() for c in result)):
                
                # Улучшаем читаемость (заменяем похожие символы)
                replacements = {
                    '0': 'О', '1': 'I', '2': 'Z', '3': 'З', 
                    '4': 'Ч', '5': 'Б', '6': 'Б', '7': 'Т',
                    '8': 'В', '9': 'Д', 'A': 'А', 'B': 'В',
                    'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К',
                    'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т',
                    'X': 'Х', 'Y': 'У'
                }
                
                cleaned_result = ''
                for char in result:
                    if char in replacements:
                        cleaned_result += replacements[char]
                    else:
                        cleaned_result += char
                
                print(f"  Очищенный текст: '{cleaned_result}'")
                results.append((x, y, w, h, cleaned_result))
                
                # Рисуем на исходном изображении
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(image, cleaned_result, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
    except Exception as e:
        print(f"  Ошибка распознавания: {e}")

# 4. ВЫВОД РЕЗУЛЬТАТОВ
print("\n" + "="*50)
if results:
    print("РАСПОЗНАННЫЕ НОМЕРА:")
    for i, (x, y, w, h, text) in enumerate(results):
        print(f"{i+1}. {text}")
else:
    print("Номерные знаки не распознаны")
    print("\nПопробуйте:")
    print("1. Улучшить качество изображения")
    print("2. Проверить освещение на фото")
    print("3. Убедиться, что номер четко виден")

# 5. ПОКАЗ РЕЗУЛЬТАТОВ
# Показываем исходное изображение с выделенными номерами
display_image = cv2.resize(image, (800, int(800 * image.shape[0] / image.shape[1])))
cv2.imshow("Результат распознавания", display_image)

# Показываем промежуточные этапы для отладки
cv2.imshow("Предобработанное изображение", cv2.resize(gray, (800, 600)))
cv2.imshow("Бинарное изображение", cv2.resize(thresh, (800, 600)))

cv2.waitKey(0)
cv2.destroyAllWindows()
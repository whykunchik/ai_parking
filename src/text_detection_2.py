import easyocr
import matplotlib.pyplot as plt
import cv2
import re

def clean_ocr_text(text):
    """
    Очищает и исправляет текст, распознанный OCR для номерных знаков
    """
    if not text:
        return ""
    
    # 1. Приводим к верхнему регистру
    text = text.upper()
    
    # 2. Убираем все не-символы (оставляем только русские/английские буквы и цифры)
    text = re.sub(r'[^A-ZА-Я0-9]', '', text)
    
    # 3. Контекстно-зависимые замены
    def smart_replace(text):
        result = []
        for i, char in enumerate(text):
            # Определяем контекст
            prev_char = text[i-1] if i > 0 else ''
            next_char = text[i+1] if i < len(text)-1 else ''
            
            # Правила для 0/О - самый частый случай
            if char in ['0', 'О', 'O']:
                # Если рядом цифры - это скорее всего 0
                if (prev_char.isdigit() or next_char.isdigit()):
                    result.append('0')
                # Если рядом буквы - это скорее всего О
                elif (prev_char.isalpha() or next_char.isalpha()):
                    result.append('О')
                # По умолчанию - 0
                else:
                    result.append('0')
            
            # Замены для других часто путаемых символов
            elif char == '1':
                # Если 1 между буквами - это скорее I
                if prev_char.isalpha() and next_char.isalpha():
                    result.append('I')
                else:
                    result.append('1')
            
            elif char == '7':
                # Если 7 между буквами - это скорее Т
                if prev_char.isalpha() and next_char.isalpha():
                    result.append('Т')
                else:
                    result.append('7')
            
            elif char == '8':
                # Если 8 между буквами - это скорее В
                if prev_char.isalpha() and next_char.isalpha():
                    result.append('В')
                else:
                    result.append('8')
            
            elif char == '4':
                # Если 4 между буквами - это скорее Ч
                if prev_char.isalpha() and next_char.isalpha():
                    result.append('Ч')
                else:
                    result.append('4')
            
            # Стандартные замены
            elif char == 'A':
                result.append('А')
            elif char == 'B':
                result.append('В')
            elif char == 'C':
                result.append('С')
            elif char == 'E':
                result.append('Е')
            elif char == 'H':
                result.append('Н')
            elif char == 'K':
                result.append('К')
            elif char == 'M':
                result.append('М')
            elif char == 'O':
                result.append('О')
            elif char == 'P':
                result.append('Р')
            elif char == 'T':
                result.append('Т')
            elif char == 'X':
                result.append('Х')
            elif char == 'Y':
                result.append('У')
            
            else:
                result.append(char)
        
        return ''.join(result)
    
    # Применяем умные замены
    text = smart_replace(text)
    
    return text

def preprocess_for_ocr(image_path):
    """
    Улучшенная предобработка изображения для OCR
    """
    # Загружаем изображение
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 1. Конвертация в серый
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Определяем, светлый или темный фон
    mean_intensity = cv2.mean(gray)[0]
    
    # 3. Если фон светлый (> 127), инвертируем (делаем текст светлым на темном)
    if mean_intensity > 127:
        gray = cv2.bitwise_not(gray)
    
    # 4. Увеличение контраста с CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 5. Убираем шум
    denoised = cv2.medianBlur(enhanced, 3)
    
    # 6. Бинаризация
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 7. Увеличение размера для лучшего распознавания
    scale_factor = 2
    new_width = binary.shape[1] * scale_factor
    new_height = binary.shape[0] * scale_factor
    resized = cv2.resize(binary, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    return resized

def use_easyocr_improved(image_path, show_image=False, use_preprocessing=True):
    """
    Улучшенная функция распознавания с постобработкой OCR
    
    Параметры:
    ----------
    image_path : str
        Путь к изображению
    show_image : bool, optional
        Показывать ли изображение при неудачном распознавании
    use_preprocessing : bool, optional
        Использовать ли улучшенную предобработку (по умолчанию True)
    
    Возвращает:
    -----------
    str или None
        Очищенный текст или None если не удалось распознать
    """
    
    # Проверка существования файла
    import os
    if not os.path.exists(image_path):
        print(f"❌ Файл не найден: {image_path}")
        return None
    
    print(f"🔍 Распознаю: {image_path}")
    
    try:
        # Улучшенная предобработка
        if use_preprocessing:
            processed_img = preprocess_for_ocr(image_path)
            if processed_img is None:
                print(f"❌ Ошибка предобработки изображения")
                return None
        else:
            # Базовая загрузка
            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Не удалось загрузить изображение")
                return None
            processed_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Инициализация EasyOCR (с кэшированием)
        if not hasattr(use_easyocr_improved, 'reader'):
            print("🔄 Инициализация EasyOCR...")
            use_easyocr_improved.reader = easyocr.Reader(['ru', 'en'], gpu=False)
        
        reader = use_easyocr_improved.reader
        
        # Распознавание с разными параметрами
        all_results = []
        
        # Пробуем разные параметры для лучшего результата
        param_combinations = [
            {'paragraph': False, 'detail': 0},  # По умолчанию
            {'paragraph': True, 'detail': 0},   # Абзацный режим
        ]
        
        for params in param_combinations:
            try:
                results = reader.readtext(processed_img, **params)
                if results:
                    if isinstance(results[0], tuple):  # Если detail=1
                        # Извлекаем только текст
                        results = [text for (bbox, text, conf) in results]
                    
                    all_results.extend(results)
            except:
                continue
        
        if all_results:
            # Объединяем все результаты
            raw_text = ' '.join(all_results).strip()
            print(f"📝 Сырой текст OCR: '{raw_text}'")
            
            # Очистка текста
            cleaned_text = clean_ocr_text(raw_text)
            print(f"🧹 Очищенный текст: '{cleaned_text}'")
            
            # Проверка на валидность номера
            if is_valid_license_plate(cleaned_text):
                print(f"✅ Валидный номер: {cleaned_text}")
                return cleaned_text
            else:
                print(f"⚠️  Некорректный формат номера, возвращаем очищенный: {cleaned_text}")
                return cleaned_text if cleaned_text else None
        else:
            print(f"❌ Текст не распознан в файле: {image_path}")
            
            # Показать изображение если нужно
            if show_image:
                try:
                    img = cv2.imread(image_path)
                    plt.figure(figsize=(10, 6))
                    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    plt.title(f"Не удалось распознать: {os.path.basename(image_path)}")
                    plt.axis('off')
                    plt.show()
                    
                    # Также покажем обработанное изображение
                    plt.figure(figsize=(10, 6))
                    plt.imshow(processed_img, cmap='gray')
                    plt.title(f"Обработанное изображение для OCR")
                    plt.axis('off')
                    plt.show()
                except Exception as e:
                    print(f"Не удалось показать изображение: {e}")
            
            return None
            
    except Exception as e:
        print(f"⚠️ Ошибка при распознавании: {str(e)}")
        return None

def is_valid_license_plate(text):
    """
    Проверяет, соответствует ли текст формату российского номерного знака
    """
    if not text or len(text) < 5:
        return False
    
    # Проверяем длину (российские номера обычно 6-9 символов)
    if not (5 <= len(text) <= 10):
        return False
    
    # Проверяем паттерны российских номеров
    patterns = [
        # Стандартный: буква-3цифры-2буквы
        r'^[АВЕКМНОРСТУХ]{1}\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        
        # Такси/коммерческий: 4цифры-2буквы
        r'^\d{4}[АВЕКМНОРСТУХ]{2}\d{2,3}$',
        
        # Старый формат: 2буквы-4цифры
        r'^[АВЕКМНОРСТУХ]{2}\d{4}\d{2,3}$',
        
        # Мотоциклы: 4цифры-2буквы (без региона)
        r'^\d{4}[АВЕКМНОРСТУХ]{2}$',
        
        # Формат с 2 цифрами региона
        r'^[АВЕКМНОРСТУХ]{1}\d{3}[АВЕКМНОРСТУХ]{2}\d{2}$',
        
        # Формат с 3 цифрами региона
        r'^[АВЕКМНОРСТУХ]{1}\d{3}[АВЕКМНОРСТУХ]{2}\d{3}$',
    ]
    
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    
    # Если не соответствует строгим паттернам, но содержит буквы и цифры
    # в разумных пропорциях - считаем валидным
    letters = sum(1 for c in text if c.isalpha() and c in 'АВЕКМНОРСТУХ')
    digits = sum(1 for c in text if c.isdigit())
    
    return letters >= 2 and digits >= 3 and (letters + digits) >= len(text) * 0.8

# Для обратной совместимости сохраняем старую функцию
def use_easyocr(image_path, show_image=False):
    """
    Старая функция для обратной совместимости
    Использует новую улучшенную версию внутри
    """
    return use_easyocr_improved(image_path, show_image, use_preprocessing=True)

# Пример использования
# if __name__ == "__main__":
#     # Тестируем функцию
#     test_file = "images/car_images/detected_plate_0_0.jpg"
#     import os
    
#     if os.path.exists(test_file):
#         print("🧪 Тестируем улучшенную функцию распознавания...")
#         result = use_easyocr_improved(test_file, show_image=True, use_preprocessing=True)
#         print(f"🎯 Итоговый результат: {result}")
        
#         # Также тестируем очистку текста отдельно
#         test_texts = [
#             "A001BC177",
#             "0ОО1ВС177",  # с ошибками OCR
#             "C333CT777",
#             "A123BC456",
#             "0ОО1ВС177 -> A001BC177",  # тест контекстной замены
#         ]
        
#         print("\n🧪 Тестируем очистку OCR текста:")
#         for test_text in test_texts:
#             cleaned = clean_ocr_text(test_text)
#             valid = is_valid_license_plate(cleaned)
#             print(f"  '{test_text}' -> '{cleaned}' {'✅' if valid else '❌'}")
#     else:
#         print(f"❌ Тестовый файл не найден: {test_file}")
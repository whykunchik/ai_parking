import cv2
from ultralytics import YOLO
import pytesseract as pytess
import os

# Установите путь к Tesseract если нужно
# pytess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytess.pytesseract.tesseract_cmd = tesseract_path
def simple_yolo_ocr(image_path, save_result=True):
    """Упрощенная версия с YOLO и OCR без отображения окон"""
    print("🚀 Запуск распознавания номеров...")
    # 1. Проверяем и загружаем модель YOLO
    model_path = "runs/detect/train/weights/best.pt"
    model = YOLO(model_path)
    
    # 2. Загружаем изображение
    image = cv2.imread(image_path)
    original_image = image.copy()
    height, width = image.shape[:2]

    
    # 3. Детекция с помощью YOLO
    results = model(image, conf=0.25, verbose=False)
    found_plates = []
    
    # 4. Обработка результатов
    for result_idx, result in enumerate(results):
        boxes = result.boxes

        if boxes is not None:
            print(f"✅ Найдено {len(boxes)} объектов")
            
            for box_idx, box in enumerate(boxes):
                # Координаты bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                
                print(f"\n🎯 Объект {box_idx + 1}:")
                print(f"   • Уверенность: {confidence:.2%}")
                print(f"   • Координаты: [{x1}, {y1}, {x2}, {y2}]")
                print(f"   • Размер: {x2-x1}x{y2-y1} пикселей")
                
                # Вырезаем номерной знак
                plate_roi = image[y1:y2, x1:x2]
                
                # Проверяем что область не пустая
                if plate_roi.size == 0:
                    print("   • Пропускаем - пустая область")
                    continue
                
                # Сохраняем вырезанный номер
                plate_filename = f"detected_plate_{result_idx}_{box_idx}.jpg"
                cv2.imwrite(plate_filename, plate_roi)
                print(f"   • Сохранен как: {plate_filename}")
                
                # 5. OCR распознавание
                try:
                    gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY) # Преобразуем в серый
                    gray = cv2.equalizeHist(gray)# Улучшаем контраст                                        
                    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)# Применяем пороговую обработку
                    
                    text = pytess.image_to_string(thresh, lang='rus+eng') # Распознаем текст
                    text = text.strip()
                    
                    # Очищаем текст от мусора
                    import re
                    cleaned_text = re.sub(r'[^-ZА-Я0-9]', '', text.upper())
                    if cleaned_text:
                        print(f"   • Распознанный текст: {cleaned_text}")
                    else:
                        print(f"   • Текст не распознан")
                    
                    found_plates.append({
                        'text': cleaned_text,
                        'confidence': confidence,
                        'bbox': (x1, y1, x2, y2),
                        'image_path': plate_filename
                    })
                    # Рисуем результат на оригинальном изображении
                    cv2.rectangle(original_image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    
                    # Добавляем текст
                    label = f"{cleaned_text} ({confidence:.2f})"
                    cv2.putText(original_image, label, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                except Exception as e:
                    print(f"   • Ошибка OCR: {e}")
        else:
            print("❌ Номерные знаки не обнаружены")
    
    # 6. Сохраняем итоговый результат
    if save_result and len(found_plates) > 0:
        result_filename = "detection_result.jpg"
        cv2.imwrite(result_filename, original_image)
        print(f"\n💾 Итоговое изображение сохранено: {result_filename}")
    
    # 7. Выводим сводку
    print("\n" + "="*50)
    print("📊 СВОДКА РЕЗУЛЬТАТОВ")
    print("="*50)
    
    if found_plates:
        print(f"✅ Найдено номерных знаков: {len(found_plates)}")
        for i, plate in enumerate(found_plates):
            print(f"\n   Номер #{i+1}:")
            print(f"   • Текст: {plate['text']}")
            print(f"   • Уверенность: {plate['confidence']:.2%}")
            print(f"   • Координаты: {plate['bbox']}")
            print(f"   • Изображение: {plate['image_path']}")
    else:
        print("❌ Номерные знаки не обнаружены")
    
    return found_plates

# ========== АЛЬТЕРНАТИВНЫЙ ВАРИАНТ (только вывод текста) ==========
def minimal_ocr_with_yolo(image_path):
    """Минимальная версия - только текст без сохранения изображений"""
    from ultralytics import YOLO
    import pytesseract as pytess
    import cv2
    
    # Загрузка модели
    model = YOLO("runs/detect/train/weights/best.pt")
    
    # Загрузка изображения
    img = cv2.imread(image_path)
    
    # Детекция
    results = model(img, conf=0.25, verbose=False)
    
    plates_text = []
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate = img[y1:y2, x1:x2]
                
                if plate.size > 0:
                    # OCR
                    gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    text = pytess.image_to_string(thresh, lang='rus+eng').strip()
                    
                    if text:
                        plates_text.append(text)
                        print(f"Распознан номер: {text}")
    
    return plates_text

# ========== ВАРИАНТ С MATPLOTLIB (если нужен просмотр) ==========
def show_with_matplotlib(image_path):
    """Версия с отображением через matplotlib (работает везде)"""
    import matplotlib.pyplot as plt
    from ultralytics import YOLO
    import cv2
    
    # Загрузка и обработка
    model = YOLO("runs/detect/train/weights/best.pt")
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Детекция
    results = model(img, conf=0.25)
    
    # Отрисовка результатов
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                
                # Рисуем прямоугольник
                import matplotlib.patches as patches
                rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, 
                                       linewidth=2, edgecolor='green', facecolor='none')
                
                # Добавляем текст
                plt.text(x1, y1-10, f"Conf: {confidence:.2f}", 
                        color='green', fontsize=10, 
                        bbox=dict(facecolor='white', alpha=0.7))
    
    # Отображение
    plt.figure(figsize=(12, 8))
    plt.imshow(img_rgb)
    plt.axis('off')
    plt.title("Результаты детекции номеров")
    plt.show()

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    # Способ 1: Простой вывод в консоль (рекомендуется)
    print("СПОСОБ 1: Простое распознавание с сохранением файлов")
    results = simple_yolo_ocr("images/image99.jpg", save_result=True)
    
    # Способ 2: Только текст
    # print("\n" + "="*60)
    # print("СПОСОБ 2: Только распознанный текст")
    # print("="*60)
    # texts = minimal_ocr_with_yolo("images/imagetesla.jpg")
    
    # Способ 3: С отображением через matplotlib (нужно установить matplotlib)
    # pip install matplotlib
    # show_with_matplotlib("images/imagetesla.jpg")
    # import cv2
    # import matplotlib.pyplot as plt



    #ВСЕ ВЫРЕЗАННЫЕ НОМЕРА
    # def analyze_detected_plates():
    #     """Анализ вырезанных номеров"""
    #     import glob
        
    #     plate_files = glob.glob("detected_plate_*.jpg")
        
    #     if not plate_files:
    #         print("❌ Файлы номеров не найдены!")
    #         return
        
    #     print(f"✅ Найдено {len(plate_files)} файлов номеров")
        
    #     for i, plate_file in enumerate(plate_files[:3]):  # покажем первые 3
    #         img = cv2.imread(plate_file)
            
    #         if img is None:
    #             print(f"  ❌ Не удалось загрузить {plate_file}")
    #             continue
            
    #         h, w = img.shape[:2]
    #         print(f"\n  📊 {plate_file}: {w}x{h} пикселей")
            
    #         # Проверяем размер - должен быть достаточно большим
    #         if w < 100 or h < 30:
    #             print(f"  ⚠️  СЛИШКОМ МАЛЕНЬКИЙ! Минимум 100x30 пикселей")
            
    #         # Покажем изображение (если установлен matplotlib)
    #         try:
    #             plt.figure(figsize=(10, 3))
    #             plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    #             plt.title(f"Номер {i+1}: {w}x{h}")
    #             plt.axis('off')
    #             plt.show()
    #         except:
    #             pass

    # analyze_detected_plates()
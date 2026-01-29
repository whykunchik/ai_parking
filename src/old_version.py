import cv2
from ultralytics import YOLO
import pytesseract as pytess
import os

# Установите путь к Tesseract если нужно
# pytess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def simple_yolo_ocr(image_path, save_result=True):

    # 1. Проверяем и загружаем модель YOLO
    model_path = "runs/detect/train/weights/best.pt"
    
    if not os.path.exists(model_path):
        print(f"❌ Модель не найдена: {model_path}")
        
        # Пробуем найти модель автоматически
        import glob
        possible_paths = glob.glob("runs/detect/**/weights/best.pt", recursive=True)
        
        if not possible_paths:
            print("❌ Обученная модель не найдена!")
            print("Сначала обучите модель: model.train(data='dataset.yaml', epochs=50)")
            return
        
        model_path = possible_paths[0]

    model = YOLO(model_path)
    
    # 2. Загружаем изображение
    if not os.path.exists(image_path):
        print(f"❌ Изображение не найдено: {image_path}")
        return
    

    image = cv2.imread(image_path)
    original_image = image.copy()
    
    if image is None:
        print("❌ Ошибка загрузки изображения!")
        return
    
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
                print(f"   • Размер: {x2-x1}x{y2-y1} пикселей")
                
                # Вырезаем номерной знак
                plate_roi = image[y1:y2, x1:x2]
                
                # Проверяем что область не пустая
                if plate_roi.size == 0:
                    print("   • Пропускаем - пустая область")
                    continue
                
                #Сохраняем вырезанный номер
                plate_filename = f"images/car_images/detected_plate_{result_idx}_{box_idx}.jpg"
                gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
                cv2.imwrite(plate_filename, gray)
                print(f"   • Сохранен как: {plate_filename}")
                
                # 5. OCR распознавание
                # try:
                #     # Преобразуем в серый
                #     gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
                    
                #     # Улучшаем контраст
                #     gray = cv2.equalizeHist(gray)
                    
                #     # Применяем пороговую обработку
                #     _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                #     # Распознаем текст
                #     text = pytess.image_to_string(thresh, lang='rus+eng')
                #     text = text.strip()
                    
                #     # Очищаем текст от мусора
                #     import re
                #     cleaned_text = re.sub(r'[^A-ZА-Я0-9]', '', text.upper())
                    
                #     if cleaned_text:
                #         print(f"   • Распознанный текст: {cleaned_text}")
                #     else:
                #         print(f"   • Текст не распознан")
                    
                #     found_plates.append({
                #         'text': cleaned_text,
                #         'confidence': confidence,
                #         'bbox': (x1, y1, x2, y2),
                #         'image_path': plate_filename
                #     })
                    
                #     # Рисуем результат на оригинальном изображении
                #     cv2.rectangle(original_image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    
                #     # Добавляем текст
                #     label = f"{cleaned_text} ({confidence:.2f})"
                #     cv2.putText(original_image, label, (x1, y1 - 10), 
                #                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                # except Exception as e:
                #     print(f"   • Ошибка OCR: {e}")
        else:
            print("❌ Номерные знаки не обнаружены")
    
    # 6. Сохраняем итоговый результат
    # if save_result and len(found_plates) > 0:
    #     result_filename = "detection_result.jpg"
    #     cv2.imwrite(result_filename, original_image)
    #     print(f"\n💾 Итоговое изображение сохранено: {result_filename}")
    
    # 7. Выводим сводку
    print("\n" + "="*50)
    print("📊 СВОДКА РЕЗУЛЬТАТОВ")
    print("="*50)
    
    if found_plates:
        print(f"✅ Найдено номерных знаков: {len(found_plates)}")
        for i, plate in enumerate(found_plates):
            print(f"\n   Номер #{i+1}:")
            print(f"   • Изображение: {plate['image_path']}")
    else:
        print("❌ Номерные знаки не обнаружены")
    
    return found_plates


# ========== ЗАПУСК ==========
# if __name__ == "__main__":
#     # Способ 1: Простой вывод в консоль (рекомендуется)
#     print("="*60)
#     print("СПОСОБ 1: Простое распознавание с сохранением файлов")
#     print("="*60)
#     results = simple_yolo_ocr("images/image99.jpg", save_result=True)
    

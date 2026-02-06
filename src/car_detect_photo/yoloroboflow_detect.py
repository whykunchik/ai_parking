import cv2
from ultralytics import YOLO
import os
from datetime import datetime

def save_detected_plate(image_path):
    """
    Args:
        image_path (str): Путь к изображению (например: "images/image99.jpg")
    
    Returns:
        list: Пути к сохраненным файлам или пустой список
    """
    
    # Проверяем существование файла
    if not os.path.exists(image_path):
        print(f"⚠️ Файл не найден: {image_path}")
        # Ищем изображение в папке images
        alt_path = f"images/{os.path.basename(image_path)}"
        if os.path.exists(alt_path):
            image_path = alt_path
            print(f"✅ Найдено по альтернативному пути: {image_path}")
        else:
            return []
    
    # Загружаем изображение
    img = cv2.imread(image_path)
    if img is None:
        return []
    
    # Создаем папку для сохранения, если не существует
    os.makedirs("images/car_images", exist_ok=True)
    
    # Загружаем модель
    model_path = "models/best.pt"
    if not os.path.exists(model_path):
        print(f"⚠️ Модель не найдена: {model_path}")
        return []
    
    model = YOLO(model_path)
    
    # Детекция
    results = model(img, conf=0.25, verbose=False)
    
    saved_files = []
    
    # Обработка каждого обнаруженного номера
    for i, r in enumerate(results):
        if r.boxes is not None:
            for j, box in enumerate(r.boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                
                # Вырезаем номер
                plate_img = img[y1:y2, x1:x2]
                
                if plate_img.size == 0:
                    continue
                
                # Создаем имя файла
                filename = f"images/car_images/plate_{i}_{j}_{int(conf*100)}.jpg"
                
                # Сохраняем
                cv2.imwrite(filename, plate_img)
                saved_files.append(filename)
    
    return saved_files


# Быстрый тест функции
if __name__ == "__main__":
    # Тестируем на вашем изображении
    files = save_detected_plate("images/image99.jpg")
    
    if files:
        print("✅ Номера сохранены:")
        for f in files:
            print(f"   → {f}")
    else:
        print("❌ Номера не найдены")
        
    # Или протестируем все изображения в папке
    """
    import glob
    all_images = glob.glob("images/*.jpg") + glob.glob("images/*.png") + glob.glob("images/*.jpeg")
    
    for img in all_images:
        print(f"\n🔍 Обработка: {img}")
        results = save_detected_plate(img)
        if results:
            print(f"   ✅ Сохранено: {len(results)} номеров")
    """
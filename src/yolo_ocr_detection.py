import cv2
from ultralytics import YOLO
import pytesseract as pytess
import os
import easyocr
import glob

from car_detect_photo.yoloroboflow_detect import save_detected_plate
from text_detect.text_detection import use_easyocr #модель для распознавания текста
from car_detect_video.video_detect import SimpleDeduplicationDetector

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytess.pytesseract.tesseract_cmd = tesseract_path

detector = SimpleDeduplicationDetector()
count = detector.process_video(video_path="src/car_detect_video/obrez.mp4")

detected_plates_folder = "detected_plates"

# Получаем все изображения из папки
plate_images = glob.glob(os.path.join(detected_plates_folder, "*.jpg"))

if not plate_images:
    print(f"❌ В папке {detected_plates_folder} не найдено изображений")
else:
    print(f"📁 Найдено {len(plate_images)} изображений для распознавания")
    print("-" * 50)
    
    # Обрабатываем каждое изображение
    for i, plate_path in enumerate(plate_images, 1):
        print(f"\n🔍 Обработка изображения {i}/{len(plate_images)}:")
        print(f"   Файл: {os.path.basename(plate_path)}")
        
        # Распознаем текст с помощью EasyOCR
        result = use_easyocr(plate_path, show_image=False)
        
        if result:
            print(f"   ✅ Распознанный текст: {result}")
        else:
            print("   ❌ Текст не распознан")

print("\n" + "=" * 50)
print(f"✅ Обработка завершена! Всего обработано: {len(plate_images)} изображений")


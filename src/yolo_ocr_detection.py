import cv2
from ultralytics import YOLO
import pytesseract as pytess
import os
import easyocr

# from car_detect.yolo_detect import simple_yolo_ocr #модель для вырезки номера
from car_detect.yoloroboflow_detect import save_detected_plate
from text_detect.text_detection import use_easyocr #модель для распознавания текста

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytess.pytesseract.tesseract_cmd = tesseract_path

results = save_detected_plate("images/image99.jpg")

if results:
    
    # 2. Для каждого сохраненного номера запускаем распознавание текста
    for i, plate_path in enumerate(results):       
        # 3. Распознаем текст на сохраненном изображении
        result = use_easyocr(plate_path, show_image=False) 
        if result:
            print(f"✅ Распознанный текст: {result}")
        else:
            print("Текст не распознан")
else:
    print("Номерные знаки не найдены")
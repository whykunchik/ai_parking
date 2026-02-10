# test_yolo.py
from ultralytics import YOLO
import cv2
import numpy as np

# 1. Тест с предобученной моделью
print("Тест с YOLOv8n...")
try:
    model = YOLO('yolov8n.pt')
    print("Модель загружена успешно!")
    
    # Тестовое изображение
    img = np.zeros((640, 640, 3), dtype=np.uint8)
    results = model(img)
    print(f"Обнаружено объектов: {len(results[0].boxes)}")
    print("Тест пройден!")
    
except Exception as e:
    print(f"Ошибка: {e}")

# 2. Тест с вашей моделью
print("\nТест с вашей моделью...")
try:
    your_model_path = "C:\ai_parking\ai_parking\models\best.pt"  # Укажите правильный путь
    model = YOLO(your_model_path)
    print("Ваша модель загружена успешно!")
except Exception as e:
    print(f"Ошибка при загрузке вашей модели: {e}")
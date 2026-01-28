import cv2
import numpy as np
import os
import random
from PIL import Image, ImageDraw, ImageFont

def create_synthetic_plate_dataset(num_images=100):
    """Создает реалистичный синтетический датасет номерных знаков"""
    
    dataset_dir = "synthetic_plates_dataset"
    os.makedirs(f"{dataset_dir}/images/train", exist_ok=True)
    os.makedirs(f"{dataset_dir}/labels/train", exist_ok=True)
    os.makedirs(f"{dataset_dir}/images/val", exist_ok=True)
    os.makedirs(f"{dataset_dir}/labels/val", exist_ok=True)
    
    # Русские буквы для номеров
    letters = "АВЕКМНОРСТУХ"
    digits = "0123456789"
    
    print(f"Создаем {num_images} синтетических изображений...")
    
    for i in range(num_images):
        # Создаем фон (разные сцены)
        bg_type = random.choice(['street', 'parking', 'garage'])
        if bg_type == 'street':
            bg_color = (random.randint(100, 150), random.randint(100, 150), random.randint(100, 150))
        elif bg_type == 'parking':
            bg_color = (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200))
        else:
            bg_color = (random.randint(50, 100), random.randint(50, 100), random.randint(50, 100))
        
        # Создаем изображение
        img = np.full((640, 640, 3), bg_color, dtype=np.uint8)
        
        # Добавляем "машину" (прямоугольник)
        car_h = random.randint(200, 400)
        car_w = random.randint(300, 500)
        car_x = random.randint(50, 640-car_w-50)
        car_y = random.randint(100, 640-car_h-100)
        car_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        cv2.rectangle(img, (car_x, car_y), (car_x+car_w, car_y+car_h), car_color, -1)
        
        # Добавляем номерной знак
        plate_h = 60
        plate_w = 240
        plate_x = car_x + random.randint(20, car_w - plate_w - 20)
        plate_y = car_y + car_h - plate_h - 20
        
        # Рисуем номер (белый прямоугольник + текст)
        cv2.rectangle(img, (plate_x, plate_y), (plate_x+plate_w, plate_y+plate_h), (255, 255, 255), -1)
        
        # Генерируем номер
        plate_text = f"{random.choice(letters)}{random.choice(digits)}{random.choice(digits)}{random.choice(digits)}{random.choice(letters)}{random.choice(letters)}"
        
        # Добавляем текст номера
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(plate_text, font, 1, 2)[0]
        text_x = plate_x + (plate_w - text_size[0]) // 2
        text_y = plate_y + plate_h // 2 + text_size[1] // 2
        cv2.putText(img, plate_text, (text_x, text_y), font, 1, (0, 0, 0), 2)
        
        # Определяем split (train/val)
        split = 'train' if i < num_images * 0.8 else 'val'
        
        # Сохраняем изображение
        img_path = f"{dataset_dir}/images/{split}/plate_{i:04d}.jpg"
        cv2.imwrite(img_path, img)
        
        # Создаем аннотацию YOLO
        label_path = f"{dataset_dir}/labels/{split}/plate_{i:04d}.txt"
        x_center = (plate_x + plate_w/2) / 640
        y_center = (plate_y + plate_h/2) / 640
        width = plate_w / 640
        height = plate_h / 640
        
        with open(label_path, 'w') as f:
            f.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        if (i+1) % 20 == 0:
            print(f"   Создано {i+1}/{num_images} изображений")
    
    # Создаем data.yaml
    yaml_content = f"""
path: {os.path.abspath(dataset_dir)}
train: images/train
val: images/val

nc: 1
names: ['license_plate']

author: Synthetic Dataset
date: 2024
"""
    
    with open(f"{dataset_dir}/data.yaml", 'w') as f:
        f.write(yaml_content)
    
    print(f"\n✅ Создано {num_images} синтетических изображений в {dataset_dir}")
    return dataset_dir

# Создаем датасет из 200 изображений
dataset_path = create_synthetic_plate_dataset(200)

# Теперь можно обучать YOLO
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.train(data=f"{dataset_path}/data.yaml", epochs=50, imgsz=640)
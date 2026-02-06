import cv2
from ultralytics import YOLO
import os
import numpy as np
from collections import defaultdict

class SimpleDeduplicationDetector:
    def __init__(self, model_path="models/best.pt", output_folder="detected_plates"):
        self.model = YOLO(model_path)
        self.output_folder = output_folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # ПРОСТАЯ дедупликация: сохраняем позицию центра
        self.saved_positions = []  # список (center_x, center_y)
        self.position_threshold = 150  # пикселей - если центр в этом радиусе, считаем тем же номером
        self.plate_counter = 0
        self.all_detections = 0  # всего детекций
        self.unique_detections = 0  # уникальных сохранений
        
    def _is_new_position(self, center_x, center_y):
        """Проверяем, не находили ли уже номер в этой области"""
        for saved_x, saved_y in self.saved_positions:
            distance = np.sqrt((center_x - saved_x)**2 + (center_y - saved_y)**2)
            if distance < self.position_threshold:
                return False  # Уже находили в этой области
        return True  # Новая область
    
    def process_video(self, video_path, confidence_threshold=0.25, frame_skip=3):
        """Обработка с ПРОСТОЙ дедупликацией по позиции"""
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Не удалось открыть видео: {video_path}")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        
        print(f"🎬 Обработка видео с простой дедупликацией")
        print(f"📊 Порог уверенности: {confidence_threshold}, пропуск кадров: {frame_skip}")
        print(f"📏 Порог дедупликации: {self.position_threshold} пикселей")
        print("-" * 50)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            if frame_count % frame_skip != 0:
                continue
            
            # Детекция
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            
            for result in results:
                if result.boxes is not None and len(result.boxes) > 0:
                    self.all_detections += len(result.boxes)
                    
                    for box in result.boxes:
                        confidence = float(box.conf[0])
                        
                        # Только уверенные детекции
                        if confidence < confidence_threshold:
                            continue
                        
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        # Вычисляем центр bounding box
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        
                        # Проверяем, не находили ли уже номер в этой области
                        if self._is_new_position(center_x, center_y):
                            # НОВЫЙ номер!
                            plate_img = frame[y1:y2, x1:x2]
                            
                            if plate_img.size == 0:
                                continue
                            
                            # Минимальный размер номера (чтобы отфильтровать шум)
                            if plate_img.shape[0] < 20 or plate_img.shape[1] < 50:
                                continue
                            
                            self.plate_counter += 1
                            self.unique_detections += 1
                            
                            # Сохраняем
                            filename = f"{self.output_folder}/plate_{self.plate_counter:03d}.jpg"
                            cv2.imwrite(filename, plate_img)
                            
                            # Сохраняем позицию для будущей дедупликации
                            self.saved_positions.append((center_x, center_y))
                            
                            print(f"✅ Уникальный номер #{self.plate_counter} сохранен!")
                            print(f"   Файл: {filename}")
                            print(f"   Кадр: {frame_count}, Время: {frame_count/fps:.2f}с")
                            print(f"   Позиция: ({center_x}, {center_y})")
                            print(f"   Уверенность: {confidence:.3f}")
                            print(f"   Размер: {plate_img.shape[1]}x{plate_img.shape[0]}")
                        else:
                            # Этот номер уже находили - НЕ сохраняем
                            print(f"⏭️  Кадр {frame_count}: номер уже найден ранее (позиция: {center_x}, {center_y})")
            
            if frame_count % 30 == 0:
                print(f"📊 Кадр {frame_count}: всего детекций {self.all_detections}, уникальных {self.unique_detections}")
        
        cap.release()
        
        print(f"\n📊 ИТОГИ:")
        print(f"Всего кадров: {frame_count}")
        print(f"Всего детекций (всех): {self.all_detections}")
        print(f"Уникальных номеров сохранено: {self.unique_detections}")
        print(f"Коэффициент дедупликации: {self.all_detections/self.unique_detections if self.unique_detections > 0 else 0:.1f}x")
        
        return self.plate_counter

# Запуск
detector = SimpleDeduplicationDetector()
count = detector.process_video(
    video_path="src/car_detect_video/obrez.mp4",
    confidence_threshold=0.2,  # НИЗКИЙ порог!
    frame_skip=2  # Обрабатывать каждый 2-й кадр
)
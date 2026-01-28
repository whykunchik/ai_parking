from ultralytics import YOLO
import torch
import os
from roboflow import Roboflow

rf = Roboflow(api_key="YOUR_API_KEY")  # получите на roboflow.com

# Выбираем проект
project = rf.workspace("license-plate-recognition-rxg4e").project("license-plate-detection")
dataset = project.version(3).download("yolov8")

# ВСЁ! Структура уже создана
print(f"Датасет скачан в: {dataset.location}")
print(f"Путь к конфигу: {dataset.location}/data.yaml")
"progsopre"


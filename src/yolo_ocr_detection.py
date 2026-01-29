import cv2
from ultralytics import YOLO
import pytesseract as pytess
import os
import easyocr

from old_version import simple_yolo_ocr #модель для вырезки номера
from text_detection import use_easyocr #модель для распознавания текста

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytess.pytesseract.tesseract_cmd = tesseract_path

results = simple_yolo_ocr("images/imagetesla.jpg", save_result=True)
use_easyocr("images/car_images/detected_plate_0_1.jpg", False)
    

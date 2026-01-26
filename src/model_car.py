import cv2
import pytesseract as pytess

image = cv2.imread("images/image99.jpg") #изображение авто

height, width, _ = image.shape #высота, ширина и профиль цвета изображения
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #делаем изображение серым

#отбираем только черные участки изображения
"""
метод оцу - автоматически вычисляет оптимальный порог
разделяем все пиксели на два класса 
все пиксели темнее определенного порога(cv2.THRESH_OTSU) становятся черными (0), светлее - белыми (255).
"""
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)[1]



#уменьшаем фото
im = thresh
target_width = 500
height, width = im.shape[:2]
aspect_ratio = width / height
target_height = int(target_width / aspect_ratio)
resized_image = cv2.resize(im, (target_width, target_height))

cv2.imshow("Zhopa", resized_image) #выводим изображение
cv2.waitKey()
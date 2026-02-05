import easyocr
import matplotlib.pyplot as plt
import cv2

def use_easyocr(image_path, show_image=False):

    reader = easyocr.Reader(['ru', 'en'], gpu = False)

    import glob

    img = cv2.imread(image_path)
    if len(img.shape) == 3:  # Цветное (height, width, channels)
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:  # Уже серое
        gray_img = img

    results = reader.readtext(gray_img, detail=0)

    if results:
        print(f"✅ Распознано: {results}")
        return results
    else:
        print(f"❌ Текст не распознан в файле: {image_path}")
        
        # Показать изображение если нужно
        if show_image:
            try:
                img = cv2.imread(image_path)
                plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                plt.title(f"Не удалось распознать: {image_path}")
                plt.show()
            except Exception as e:
                print(f"Не удалось показать изображение: {e}")


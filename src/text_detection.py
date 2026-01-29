import easyocr
import matplotlib.pyplot as plt
import cv2

def use_easyocr(image_path, show_image=False):

    reader = easyocr.Reader(['ru', 'en'], gpu = False)

    import glob
    # plate_files = glob.glob("detected_plate_0_0.jpg") + glob.glob("ocr_debug/plate_*_processed.jpg")

    # if not plate_files:
    #     print("Файлов нет")

    # for file in plate_files:
    #     results = reader.readtext(file, detail=0)
    #     if results:
    #         print(results)
    #     else:
    #         print("Ничего не найдено")

    #         try:
    #             import matplotlib.pyplot as plt
    #             import cv2
    #             img = cv2.imread(file)
    #             plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    #             plt.title("")
    #             plt.show()
    #         except:
    #             pass
    # return results

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


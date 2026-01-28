import easyocr

def use_easyocr():

    reader = easyocr.Reader(['ru', 'en'], gpu = False)

    import glob
    plate_files = glob.glob("detected_plate_0_0.jpg") + glob.glob("ocr_debug/plate_*_processed.jpg")

    if not plate_files:
        print("Файлов нет")

    for file in plate_files:
        results = reader.readtext(file, detail=0)
        if results:
            print(results)
        else:
            print("Ничего не найдено")

            try:
                import matplotlib.pyplot as plt
                import cv2
                img = cv2.imread(file)
                plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                plt.title("")
                plt.show()
            except:
                pass
    return results
use_easyocr()
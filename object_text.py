import cv2
import easyocr
import polars as pl
import numpy as np
from PIL import Image, ImageDraw, ImageFont  # Импортируем необходимые модули

def process_video(video_path, output_video_path, output_csv_path):
    # Инициализация EasyOCR с поддержкой русского языка
    reader = easyocr.Reader(['ru', 'en'], gpu=False)  # Добавиление языка и включение GPU

    # Открываем видеофайл
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Ошибка при открытии видеофайла.")
        return

    # Получаем свойства видео
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Подготовка VideoWriter для сохранения аннотированного видео
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    # Список для хранения данных для CSV
    data = []

    # Загрузка шрифта с поддержкой русского языка
    font_path = 'font/Arial.ttf'  # Укажите путь к вашему шрифту
    font_size = 20
    font = ImageFont.truetype(font_path, font_size)

    frame_number = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Распознавание текста на кадре
        results = reader.readtext(frame)

        # Преобразуем кадр OpenCV в изображение PIL
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(frame_pil)

        # Обработка результатов
        for bbox, text, conf in results:
            # Преобразование координат в целые числа
            bbox = np.array(bbox).astype(int)

            # Рисование рамки вокруг текста
            draw.line([tuple(bbox[0]), tuple(bbox[1]), tuple(bbox[2]), tuple(bbox[3]), tuple(bbox[0])],
                      fill=(0, 255, 0), width=2)

            # Вывод распознанного текста с использованием PIL
            x, y = bbox[0]
            draw.text((x, y - font_size), text, font=font, fill=(0, 255, 0))

            # Вычисление координат и размеров рамки
            x_min, y_min = bbox.min(axis=0)
            x_max, y_max = bbox.max(axis=0)
            width, height = x_max - x_min, y_max - y_min

            # Добавление данных в список
            data.append({
                'Frame': frame_number,
                'Text': text,
                'X': int(x_min),
                'Y': int(y_min),
                'Width': int(width),
                'Height': int(height)
            })

        # Преобразуем изображение PIL обратно в кадр OpenCV
        frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

        # Запись аннотированного кадра в выходное видео
        out.write(frame)

        # Отображение кадра в реальном времени
        cv2.imshow('Annotated Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_number += 1

    # Освобождение ресурсов
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # Сохранение данных в CSV файл с помощью polars
    df = pl.DataFrame(data)
    df.write_csv(output_csv_path)

if __name__ == "__main__":
    # Укажите пути к файлам здесь
    input_video = 'test_videos/text_detect.mp4'      
    output_video = 'output_videos/annotated_output.mp4'         
    output_csv = 'annotations/annotations.csv'              

    process_video(input_video, output_video, output_csv)
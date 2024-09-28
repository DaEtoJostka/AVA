import cv2
from ultralytics import YOLO
import polars as pl
import os
import numpy as np
from tqdm import tqdm 

# Путь к входному видео
input_video_path = 'test_videos/test.mp4'

# Путь для сохранения выходного видео
output_video_path = 'output_videos/detection_video.mp4'

# Путь для сохранения аннотаций
annotations_path = 'annotations/annotations_detection.csv'

# Загрузка модели
model = YOLO('weights/yolov10s.pt')

# Открытие видео
cap = cv2.VideoCapture(input_video_path)

if not cap.isOpened():
    print(f"Не удалось открыть видео: {input_video_path}")
    exit()

# Получение параметров видео
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Настройка видео-записи
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

# Инициализация списков для аннотаций
frames = []
classes = []
confidences = []
x1_list = []
y1_list = []
x2_list = []
y2_list = []

frame_count = 0

# Использование tqdm для отображения прогресса
for _ in tqdm(range(total_frames), desc="Обработка видео"):
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # Выполнение детекции
    results = model(frame, verbose=False)  # Отключение вывода прогресс-баров внутри модели

    # Обработка результатов
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        for box in boxes:
            cls = int(box.cls[0])
            confidence = float(box.conf[0])
            # Получение координат рамки
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            # Получение названия класса
            class_name = model.names[cls]

            # Добавление данных в отдельные списки
            frames.append(frame_count)
            classes.append(class_name)
            confidences.append(confidence)
            x1_list.append(x1)
            y1_list.append(y1)
            x2_list.append(x2)
            y2_list.append(y2)

            # Рисование рамки и подписи на кадре
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"{class_name} {confidence:.2f}"
            (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (int(x1), int(y1) - label_height - baseline), 
                                 (int(x1) + label_width, int(y1)), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, label, (int(x1), int(y1) - baseline), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Запись обработанного кадра в выходное видео
    out.write(frame)

    # Отображение кадра (опционально, можно отключить для ускорения)
    # cv2.imshow('YOLOv8 Detection', frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

# Освобождение ресурсов
cap.release()
out.release()
cv2.destroyAllWindows()

# Создание DataFramа с аннотациями
df = pl.DataFrame({
    'frame': frames,
    'class': classes,
    'confidence': confidences,
    'x1': x1_list,
    'y1': y1_list,
    'x2': x2_list,
    'y2': y2_list
})

# Сохранение аннотаций в CSV файл
df.write_csv(annotations_path)

print(f"Аннотации сохранены в {annotations_path}")
print(f"Выходное видео сохранено в {output_video_path}")
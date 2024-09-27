import cv2
from ultralytics import YOLO
import pandas as pd
import os

# Путь к входному видео
input_video_path = 'input_video.mp4'

# Путь для сохранения выходного видео
output_video_path = 'output_video.mp4'

# Путь для сохранения аннотаций
annotations_path = 'annotations.csv'

# Загрузка модели весов модели
model = YOLO('yolov8s.pt')

# Открытие видео
cap = cv2.VideoCapture(input_video_path)

if not cap.isOpened():
    print(f"Не удалось открыть видео: {input_video_path}")
    exit()

# Получение параметров видео
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Настройка видео-записи
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Можно использовать другой кодек
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

# Список для хранения аннотаций
annotations = []

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # Выполнение детекции
    results = model(frame)

    # Обработка результатов
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            confidence = float(box.conf[0])
            # Получение координат рамки
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            # Получение названия класса
            class_name = model.names[cls]

            # Добавление аннотации
            annotations.append({
                'frame': frame_count,
                'class': class_name,
                'confidence': confidence,
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            })

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

    # Отображение кадра
    cv2.imshow('YOLOv8 Detection', frame)

    # Прерывание по нажатию клавиши 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение ресурсов
cap.release()
out.release()
cv2.destroyAllWindows()

# Сохранение аннотаций в CSV файл
df = pd.DataFrame(annotations)
df.to_csv(annotations_path, index=False)

print(f"Аннотации сохранены в {annotations_path}")
print(f"Выходное видео сохранено в {output_video_path}")
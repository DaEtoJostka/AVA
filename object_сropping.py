import cv2
import os
from ultralytics import YOLO

# Инициализируем модель YOLOv8
model = YOLO('weights/yolov10n.pt')

# Открываем видеофайл
video_path = 'test_videos/road.mp4'
cap = cv2.VideoCapture(video_path)

# Создаем общую папку для обрезков
crops_dir = 'crops'
os.makedirs(crops_dir, exist_ok=True)

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break  # Выходим из цикла, если кадры закончились

    frame_count += 1
    print(f"Обработка кадра {frame_count}")

    # Обнаружение объектов на текущем кадре
    results = model(frame)

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()  # Координаты боксов
        scores = result.boxes.conf.cpu().numpy()  # Доверительные оценки
        labels = result.boxes.cls.cpu().numpy().astype(int)  # Метки классов

        for box, score, label in zip(boxes, scores, labels):
            x1, y1, x2, y2 = map(int, box)
            cropped_object = frame[y1:y2, x1:x2]

            label_name = model.names[label]  # Получаем имя класса
            label_dir = os.path.join(crops_dir, label_name)
            os.makedirs(label_dir, exist_ok=True)

            # Сохраняем обрезанный объект
            crop_filename = f"{label_name}_{frame_count}_{score:.2f}.jpg"
            crop_path = os.path.join(label_dir, crop_filename)
            cv2.imwrite(crop_path, cropped_object)

            # Рисуем B-боксы на кадре
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Зеленый цвет, толщина 2
            cv2.putText(frame, f"{label_name} {score:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (0, 255, 0), 2)  # Отображаем метку и доверие над боксом

    # Отображаем кадр с боксов
    cv2.imshow('Frame with B-Boxes', frame)

    # Нажмите 'q' для выхода
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
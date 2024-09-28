import cv2
import numpy as np
import polars as pl

def decode_predictions(scores, geometry, scoreThresh):
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    for y in range(numRows):
        # Извлечение данных
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(numCols):
            score = scoresData[x]

            if score < scoreThresh:
                continue

            # Вычисление геометрии рамки
            offsetX, offsetY = x * 4.0, y * 4.0
            angle = anglesData[x]
            cosA = np.cos(angle)
            sinA = np.sin(angle)
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            endX = int(offsetX + (cosA * xData1[x]) + (sinA * xData2[x]))
            endY = int(offsetY - (sinA * xData1[x]) + (cosA * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            rects.append((startX, startY, endX, endY))
            confidences.append(float(score))

    return rects, confidences

# Путь к EAST модели
east_model = 'weights/frozen_east_text_detection.pb'

# Входное видео
input_video_path = 'test_videos/text_detect.mp4'

# Выходное видео
output_video_path = 'output_videos/text_detection_annotated_video.mp4'

# CSV файл для аннотаций
csv_output_path = 'annotations/text_detection_annotations.csv'

# Загрузка модели EAST
net = cv2.dnn.readNet(east_model)

# Захват видео
cap = cv2.VideoCapture(input_video_path)

# Параметры видео
fps = cap.get(cv2.CAP_PROP_FPS)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Инициализация VideoWriter
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# Список для хранения данных аннотаций
annotations = []

frame_num = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_num += 1
    orig = frame.copy()
    (H, W) = frame.shape[:2]

    # Новые размеры (кратные 32)
    newW, newH = (W // 32) * 32, (H // 32) * 32
    rW, rH = W / float(newW), H / float(newH)

    frame_resized = cv2.resize(frame, (newW, newH))

    blob = cv2.dnn.blobFromImage(frame_resized, 1.0, (newW, newH),
                                 (123.68, 116.78, 103.94), swapRB=True, crop=False)
    net.setInput(blob)

    # Получение выходных слоев
    (scores, geometry) = net.forward(['feature_fusion/Conv_7/Sigmoid', 'feature_fusion/concat_3'])

    # Декодирование предсказаний
    (rects, confidences) = decode_predictions(scores, geometry, 0.5)

    # Применение Non-Max Suppression
    indices = cv2.dnn.NMSBoxes(rects, confidences, 0.5, 0.4)

    for i in indices:
        (startX, startY, endX, endY) = rects[i]
        # Коррекция координат
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        # Рисование прямоугольника
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

        # Добавление в аннотации
        annotations.append({
            'frame': frame_num,
            'confidence': confidences[i],
            'startX': startX,
            'startY': startY,
            'endX': endX,
            'endY': endY
        })

    # Запись кадра в выходное видео
    out.write(frame)


    cv2.imshow('Text Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение ресурсов
cap.release()
out.release()
cv2.destroyAllWindows()

# Создание DataFrame и сохранение в CSV
df = pl.DataFrame(annotations)
df.write_csv(csv_output_path)
import cv2

from ultralytics import YOLO, solutions

model = YOLO("weights/yolov10s.pt")
names = model.model.names

cap = cv2.VideoCapture("test_videos/test.mp4")
assert cap.isOpened(), "Ошибка в чтении файла"
w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))

# Запись видео
video_writer = cv2.VideoWriter("distance_calculation.avi", cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

# Инициализация просчета дистанции
dist_obj = solutions.DistanceCalculation(names=names, view_img=True)

while cap.isOpened():
    success, im0 = cap.read()
    if not success:
        print("Кадр видео пустой или обработка видео прошла успешно.")
        break

    tracks = model.track(im0, persist=True, show=False)
    im0 = dist_obj.start_process(im0, tracks)
    video_writer.write(im0)

cap.release()
video_writer.release()
cv2.destroyAllWindows()
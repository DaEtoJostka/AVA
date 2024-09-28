import cv2

from ultralytics import YOLO, solutions

model = YOLO("weights/yolov10n.pt")
names = model.model.names

cap = cv2.VideoCapture("test_videos/road.mp4")
assert cap.isOpened(), "Ошибка при чтении видеофайла"
w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))

video_writer = cv2.VideoWriter("speed_estimation.avi", cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

line_pts = [(0, 360), (1280, 360)]

speed_obj = solutions.SpeedEstimator(
    reg_pts=line_pts,
    names=names,
    view_img=True,
)

while cap.isOpened():
    success, im0 = cap.read()
    if not success:
        print("Кадр видео пустой или обработка видео прошла успешно.")
        break

    tracks = model.track(im0, persist=True)

    im0 = speed_obj.estimate_speed(im0, tracks)
    video_writer.write(im0)

cap.release()
video_writer.release()
cv2.destroyAllWindows()
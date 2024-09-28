import cv2
import mediapipe as mp
import polars as pl
from tqdm import tqdm

def main(input_video_path, output_video_path, output_csv_path):
    # Инициализация Mediapipe для отслеживания лица
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False,
                                      max_num_faces=1,
                                      refine_landmarks=True,
                                      min_detection_confidence=0.6,
                                      min_tracking_confidence=0.6)

    # Инициализация инструментов рисования
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    # Захват видео
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Не удалось открыть видео: {input_video_path}")
        return

    # Получение параметров видео
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Настройка записи видео
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    # Список для хранения аннотаций
    annotations = []

    # Обработка кадров с прогресс-баром
    for frame_num in tqdm(range(total_frames), desc="Обработка видео"):
        ret, frame = cap.read()
        if not ret:
            break

        # Конвертация цвета для Mediapipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_id, face_landmarks in enumerate(results.multi_face_landmarks, start=1):
                # Рисование маски лица
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                        .get_default_face_mesh_tesselation_style())

                # Извлечение координат точек маски лица
                landmarks = []
                for landmark in face_landmarks.landmark:
                    x = landmark.x * frame_width
                    y = landmark.y * frame_height
                    z = landmark.z  # Z-координата может быть полезна для глубины
                    landmarks.extend([x, y, z])

                # Создание словаря аннотации для текущего лица
                annotation = {
                    "frame": frame_num,
                    "face_id": face_id
                }

                # Добавление координат точек маски лица
                for idx in range(0, len(landmarks), 3):
                    annotation[f"landmark_{idx//3}_x"] = landmarks[idx]
                    annotation[f"landmark_{idx//3}_y"] = landmarks[idx + 1]
                    annotation[f"landmark_{idx//3}_z"] = landmarks[idx + 2]

                annotations.append(annotation)

        # Запись кадра в выходное видео
        out.write(frame)

    # Освобождение ресурсов
    cap.release()
    out.release()

    if annotations:
        df = pl.DataFrame(annotations)
        df.write_csv(output_csv_path)
        print(f"Обработка завершена. Аннотированное видео сохранено как {output_video_path}")
        print(f"Аннотации сохранены в {output_csv_path}")
    else:
        print("Лица не обнаружены в видео. CSV-файл не создан.")

if __name__ == "__main__":
    # Путь к входному видео
    input_video = "gasprom.mp4"

    # Путь к выходному видео
    output_video = "annotated_video.mp4"

    # Путь к выходному CSV
    output_csv = "mask_annotations.csv"

    main(input_video, output_video, output_csv)
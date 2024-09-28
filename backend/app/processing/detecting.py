import sys
import logging
import uuid
import tempfile
import cv2
import ffmpeg
import torch.cuda
from ultralytics import YOLO
import polars as pl
from tqdm import tqdm
from typing import Optional
from uuid import uuid4
import subprocess

from infra.minio_client import MinioClient
from pathlib import Path

minio_client = MinioClient()


def setup_logging() -> None:
    """Setup logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compress_video(input_file: str, output_file: str, crf: int = 23, preset: str = 'medium') -> None:
    """Compress the video using ffmpeg."""
    try:
        command = ['ffmpeg', '-i', input_file, '-vcodec', 'libx264',
            '-crf', str(crf),
            '-preset', preset,
            '-acodec', 'aac',
            '-b:a', '128k',
            '-y',
            output_file]

        subprocess.run(command, check=True)
        '''(ffmpeg
        .input(input_file)
        .output(
                output_file,
                vcodec='libx264',
                crf=crf,
                preset=preset,
                acodec='aac',
                audio_bitrate='128k'
        )
        .run(overwrite_output=True))'''
        logging.info(f"Video successfully compressed and saved as {output_file}")
    except Exception as e:
        logging.error(e)
    '''except ffmpeg.Error as e:
        logging.error(f"Error compressing video: {e.stderr.decode()}")'''


def process_video(input_video: str, output_video: str, annotations_path: str) -> None:
    """Process the video, perform detection, and save annotations."""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = YOLO('app/ml_models/yolov10s.pt').to(device)

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        logging.error(f"Failed to open video: {input_video}")
        sys.exit(1)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))
    frames: list[int] = []
    classes: list[str] = []
    confidences: list[float] = []
    x1_list: list[float] = []
    y1_list: list[float] = []
    x2_list: list[float] = []
    y2_list: list[float] = []

    frame_count = 0

    for _ in tqdm(range(total_frames), desc="Processing video"):
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        results = model(frame, verbose=False)

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls = int(box.cls[0])
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                class_name = model.names[cls]

                frames.append(frame_count)
                classes.append(class_name)
                confidences.append(confidence)
                x1_list.append(x1)
                y1_list.append(y1)
                x2_list.append(x2)
                y2_list.append(y2)

                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                label = f"{class_name} {confidence:.2f}"
                (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(frame, (int(x1), int(y1) - label_height - baseline),
                              (int(x1) + label_width, int(y1)), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, label, (int(x1), int(y1) - baseline),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    df = pl.DataFrame({
        'frame': frames,
        'class': classes,
        'confidence': confidences,
        'x1': x1_list,
        'y1': y1_list,
        'x2': x2_list,
        'y2': y2_list
    })

    df.write_csv(annotations_path)
    logging.info(f"Annotations saved to {annotations_path}")
    logging.info(f"Output video saved to {output_video}")


def bbox_detect(input_video: str, output_video: str, compressed_video: str,
                annotations: Optional[str] = 'annotations.csv') -> None:
    """Main function to process and compress video."""
    setup_logging()
    logging.info(f"Input video: {input_video}")
    logging.info(f"Output video: {output_video}")
    logging.info(f"Compressed video: {compressed_video}")
    logging.info(f"Annotations path: {annotations}")

    with (
        tempfile.NamedTemporaryFile(suffix='.mp4', mode='wb+', delete=False) as input_file,
        tempfile.NamedTemporaryFile(suffix='.mp4', mode='wb+', delete=False) as output_file,
        tempfile.NamedTemporaryFile(suffix='.mp4', mode='wb+', delete=False) as compressed_file
    ):
        input_file.write(minio_client.get_file('ava', input_video, ).data)
        process_video(input_file.name, output_file.name, annotations)
        compress_video(output_file.name, compressed_file.name, crf=23, preset='medium')
        compressed_file.seek(0)
        result = compressed_file.read()

        minio_client.put_file('ava', compressed_video, result, length=len(result))

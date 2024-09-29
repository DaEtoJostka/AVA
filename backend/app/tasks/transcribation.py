import io
import tempfile
import time
from uuid import uuid4

import cv2
from scenedetect import FrameTimecode, detect, AdaptiveDetector
from sqlalchemy.orm import Session
from database import SessionLocal
# from app.models import Video
import logging

from models import Video, VideoStatus
from processing.detecting import bbox_detect

from models import Scene

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from dramatiq_broker import dramatiq
from infra.minio_client import MinioClient
from processing.transcribation import get_scenes, Transcribation

minio_client = MinioClient()
transcribation = Transcribation()


@dramatiq.actor(actor_name='transcribation_video_success')
def transcribation_video_success(message, exception):
    session = SessionLocal()
    try:
        url = message.kwargs.get("url")
        if not url:
            raise ValueError("url не передан в задаче.")

        video = session.query(Video).where(Video.url == url).first()
        if not video:
            raise ValueError(f"Видео с ID {url} не найдено.")

        video.status = VideoStatus.COMPLETED
        session.commit()
        print(f"Видео {url} помечено как FAILED из-за ошибки: {exception}")
    except Exception as e:
        session.rollback()
    finally:
        session.close()


@dramatiq.actor(actor_name='transcribation_video_failure')
def transcribation_video_failure(message, exception):
    session = SessionLocal()
    try:
        url = message["kwargs"].get("url")
        if not url:
            raise ValueError("url не передан в задаче.")

        video = session.query(Video).where(Video.url == url).first()
        if not video:
            raise ValueError(f"Видео с ID {url} не найдено.")

        video.status = VideoStatus.FAILED
        session.commit()
        print(f"Видео {url} помечено как FAILED из-за ошибки: {exception}")
    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении статуса видео {url} на FAILED: {e}")
    finally:
        session.close()


def run_transcribation_video(url: str):
    transcribation_video_task.send_with_options(
        kwargs={'url': url},
        on_success=transcribation_video_success,
        on_failure=transcribation_video_failure,
    )


@dramatiq.actor(max_retries=0, queue_name="default")
def transcribation_video_task(url: str):
    logger.info(f"Started processing video with URL: {url}")

    with ( tempfile.NamedTemporaryFile(suffix='.mp4', mode='wb+', delete=False) as video_file, ):
        video_file.write(minio_client.get_file('ava', url).data)

    if scenes := detect(video_file.name, AdaptiveDetector(),show_progress=True,start_in_scene=True):
            logger.info("Сцены есть, считаем")
            scenes: list[tuple[FrameTimecode, FrameTimecode]]
            frames = []
            video_capture = cv2.VideoCapture(video_file.name)

            audio_scenes = transcribation.get_audio_scenes(video_file.name, scenes)
            texts = transcribation.get_texts(audio_scenes)

            scenes_db_models = []
            for scene, text in zip(scenes, texts):
                logger.info("1, 2, 3")
                start_time = scene[0].get_seconds()
                end_time = scene[1].get_seconds()
                start_frame = scene[0].get_frames()
                end_frame = scene[1].get_frames()
                start_fps = scene[0].get_framerate()
                end_fps = scene[1].get_framerate()

                video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

                success, frame = video_capture.read()

                if success:
                    success, encoded_image = cv2.imencode('.jpg', frame)
                    frames.append(encoded_image)

                    minio_client.put_file(
                        'ava',
                        f'{url}_scene_{start_frame}_{end_frame}.jpg',
                        encoded_image.tobytes(),
                        len(encoded_image.tobytes()),
                        # length=len(image_bytes.getvalue()),
                        # content_type='image/jpeg'
                    )

                scene_obj = Scene(
                    id=uuid4(),
                    video_id=url,
                    start_timecode=start_time,
                    end_timecode=end_time,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    start_fps=start_fps,
                    end_fps=end_fps,
                    text=text['text'],
                )
                scenes_db_models.append(scene_obj)
            with SessionLocal() as s:
                s.bulk_save_objects(scenes_db_models)
                s.commit()

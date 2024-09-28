import time
from sqlalchemy.orm import Session
from database import SessionLocal
# from app.models import Video
import logging

from models import Video, VideoStatus
from processing.detecting import bbox_detect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from dramatiq_broker import dramatiq
from infra.minio_client import MinioClient

minio_client = MinioClient()
from processing.transcribation import get_scenes, Transcribation

@dramatiq.actor(actor_name='transcribation_video_success')
def process_video_success(message, exception):
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
def process_video_failure(message, exception):
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
    process_video_task.send_with_options(
        kwargs={'url': url},
        on_success=process_video_success,
        on_failure=process_video_failure,
    )


@dramatiq.actor(max_retries=0, queue_name="default")
def process_video_task(url: str):
    logger.info(f"Started processing video with URL: {url}")
    bbox_detect(
        input_video=url,
        output_video=f'{url}_detected',
        compressed_video=f'{url}_detected_compressed',
        annotations='cococo.csv',
    )

    session = SessionLocal()
    try:
        video = session.query(Video).where(Video.url == url).first()
        if not video:
            raise ValueError(f"Видео с ID {url} не найдено.")

        video.detected_url = f'{url}_detected_compressed'
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()
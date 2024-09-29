from asyncio.log import logger
from typing import List
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, SessionLocal
from dependencies import get_db

# models.Base.metadata.create_all(bind=engine)
from tasks import video as video_task
from tasks import transcribation as transcribation_task

fastapi_app = FastAPI()


@fastapi_app.post("/api/v1/video", )
def process_video(process_video: schemas.VideoCreate, db: Session = Depends(get_db)):
    session = SessionLocal()
    new_video = models.Video(
        id=process_video.url,
        url=process_video.url,
        detected_url=None,
        name=process_video.name,
        meta={},
    )
    session.add(new_video)
    session.commit()
    session.refresh(new_video)
    video_task.run_process_video(new_video.url)
    transcribation_task.run_transcribation_video(new_video.url)
    logger.info(f"Added new video with URL: {new_video.id}")
    return {}


@fastapi_app.get("/api/v1/video", )
def get_video(response_model=List[schemas.Video], db: Session = Depends(get_db)):
    videos = db.query(models.Video).all()
    return videos


@fastapi_app.get("/api/v1/video/scene", )
def get_scenes(video_id: UUID, db: Session = Depends(get_db)):
    scenes = db.query(models.Scene).filter(models.Scene.video_id == video_id).all()

    if not scenes:
        raise HTTPException(status_code=404, detail="Scenes not found for the given video ID")

    return scenes

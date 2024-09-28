from asyncio.log import logger
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, SessionLocal
from dependencies import get_db

# models.Base.metadata.create_all(bind=engine)
from tasks import video as video_task

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
    logger.info(f"Added new video with URL: {new_video.id}")

    return {}


@fastapi_app.get("/api/v1/video", )
def get_video(response_model=List[schemas.Video], db: Session = Depends(get_db)):
    session = SessionLocal()
    videos = db.query(models.Video).all()
    return videos

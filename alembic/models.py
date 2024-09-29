import enum

from sqlalchemy import Column, BigInteger, Text, UUID, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base


class VideoStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(Base):
    __tablename__ = 'video'

    id = Column(UUID, primary_key=True, index=True)
    url = Column(Text, nullable=False, index=True)
    detected_url = Column(Text, nullable=True, index=True)
    name = Column(Text, nullable=False, index=True)
    meta = Column(JSONB)
    progress = Column(Float, default=0.0, nullable=False)
    status = Column(Text, default="Pending", nullable=False)

    scenes = relationship("Scene", back_populates="video", cascade="all, delete-orphan")


class Scene(Base):
    __tablename__ = 'scene'

    id = Column(UUID, primary_key=True, index=True)
    video_id = Column(UUID, ForeignKey('video.id'), nullable=False)
    start_timecode = Column(Float, nullable=False)
    end_timecode = Column(Float, nullable=False)
    start_frame = Column(BigInteger, nullable=False)
    end_frame = Column(BigInteger, nullable=False)
    start_fps = Column(Float, nullable=False)
    end_fps = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    text_emotion = Column(Text, nullable=False)
    audio_emotion = Column(Text, nullable=False)
    image_emotion = Column(Text, nullable=False)
    scene_emotion = Column(Text, nullable=False)
    main_emotion = Column(Text, nullable=False)

    video = relationship("Video", back_populates="scenes")

import enum

from sqlalchemy import Column, BigInteger, Text, UUID, Float
from sqlalchemy.dialects.postgresql import JSONB
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
    progress = Column(Float, default=0.0, nullable=False)  # New field
    status = Column(Text, default="Pending", nullable=False)  # New field

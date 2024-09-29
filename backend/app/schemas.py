from uuid import UUID

from pydantic import BaseModel


class VideoBase(BaseModel):
    url: str
    name: str


class VideoCreate(VideoBase):
    pass


class Video(VideoBase):
    pass


class SceneResponse(BaseModel):
    id: UUID
    video_id: UUID
    start_timecode: float
    end_timecode: float
    start_frame: int
    end_frame: int
    start_fps: float
    end_fps: float
    text: str

    class Config:
        orm_mode = True

from pydantic import BaseModel


class VideoBase(BaseModel):
    url: str
    name: str


class VideoCreate(VideoBase):
    pass


class Video(VideoBase):
    pass

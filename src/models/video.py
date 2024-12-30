from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from src.db import db


@dataclass
class Video(db.Model):
    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("user.id"), nullable=False)
    yt_link: str = Column(String, nullable=False)
    status: str = Column(String, nullable=False, default="pending")
    title: str = Column(String, nullable=True)
    length: int = Column(Integer, nullable=True)
    views: str = Column(String, nullable=True)
    thumbnail_url: str = Column(String, nullable=True)
    description: str = Column(String, nullable=True)
    keywords: str = Column(String, nullable=True)  # will be comma seperate values
    rating: float = Column(Float, nullable=True)
    author: str = Column(String, nullable=True)
    channel_url: str = Column(String, nullable=True)
    transcript: str = Column(String, nullable=True)
    prompt_response: str = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "yt_link": self.yt_link,
            "status": self.status,
            "title": self.title,
            "length": self.length,
            "views": self.views,
            "thumbnail_url": self.thumbnail_url,
            "description": self.description,
            "keywords": self.keywords,
            "rating": self.rating,
            "author": self.author,
            "channel_url": self.channel_url,
            "transcript": self.transcript,
            "prompt_response": self.prompt_response,
            "created_at": self.created_at,
        }

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
    views: int = Column(Integer, nullable=True)
    thumbnail_url: str = Column(String, nullable=True)
    description: str = Column(String, nullable=True)
    keywords: str = Column(String, nullable=True) # will be comma seperate values
    rating: float = Column(Float, nullable=True)
    author: str = Column(String, nullable=True)
    channel_url: str = Column(String, nullable=True)
    transcript: str = Column(String, nullable=True)
    prompt_response: str = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.now(timezone.utc))

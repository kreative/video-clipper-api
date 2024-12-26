from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from src.db import db


@dataclass
class User(db.Model):
    id: int = Column(Integer, primary_key=True)
    prompt: str = Column(String, nullable=False)
    markdown_template: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.now(timezone.utc))

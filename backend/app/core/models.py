from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    status: Mapped[str] = mapped_column(String(32), default="success")  # success, error
    category: Mapped[str] = mapped_column(String(64), default="screw")
    model_name: Mapped[str] = mapped_column(String(64), default="patchcore-screw")
    model_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    
    prediction: Mapped[str] = mapped_column(String(32))  # NORMAL, ANOMALY, UNCERTAIN
    anomaly_score_raw: Mapped[float] = mapped_column(Float)
    display_score: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    inference_ms: Mapped[float] = mapped_column(Float)
    
    image_width: Mapped[int] = mapped_column(Integer)
    image_height: Mapped[int] = mapped_column(Integer)
    
    heatmap_png_base64: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

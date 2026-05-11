from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base


class ContentType(enum.Enum):
    PDF = "pdf"
    TEXT = "text"
    DOCUMENT = "document"


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(Enum(ContentType), default=ContentType.TEXT)
    file_path = Column(String(500), nullable=True)  # For PDFs
    text_content = Column(Text, nullable=True)  # For text content
    subject = Column(String(100), nullable=True)
    grade_level = Column(String(50), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    uploader = relationship("User", backref="uploaded_contents")
    quizzes = relationship("Quiz", backref="content", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}')>"
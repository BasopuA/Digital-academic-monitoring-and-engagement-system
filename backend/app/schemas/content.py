from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.content import ContentType


class ContentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=100)
    grade_level: Optional[str] = Field(None, max_length=50)


class ContentCreate(ContentBase):
    content_type: ContentType = ContentType.TEXT
    text_content: Optional[str] = None
    # file_path will be set after upload


class ContentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    is_active: Optional[bool] = None


class ContentResponse(ContentBase):
    id: int
    content_type: ContentType
    file_path: Optional[str]
    text_content: Optional[str]
    uploaded_by: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    quiz_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ContentUploadResponse(BaseModel):
    id: int
    title: str
    file_path: str
    content_type: str
    message: str
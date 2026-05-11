from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.quiz import QuestionType


# Question Schemas
class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=10)
    question_type: QuestionType
    marks: int = Field(default=1, ge=1)
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    order_index: int = 0


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: int
    quiz_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionWithoutAnswer(BaseModel):
    id: int
    question_text: str
    question_type: QuestionType
    marks: int
    options: Optional[List[str]] = None
    order_index: int

    model_config = ConfigDict(from_attributes=True)


# Quiz Schemas
class QuizBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1)


class QuizCreate(QuizBase):
    content_id: int
    is_ai_generated: bool = True


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class QuizResponse(QuizBase):
    id: int
    content_id: int
    created_by: int
    is_ai_generated: bool
    is_active: bool
    total_marks: int
    question_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class QuizDetailResponse(QuizResponse):
    questions: List[QuestionWithoutAnswer] = []


# AI Quiz Generation
class QuizGenerationRequest(BaseModel):
    content_id: int
    num_questions: int = Field(default=10, ge=1, le=50)
    question_types: Optional[List[QuestionType]] = None
    difficulty: Optional[str] = Field(default="medium", pattern="^(easy|medium|hard)$")


class QuizGenerationResponse(BaseModel):
    quiz_id: int
    title: str
    questions_generated: int
    message: str


# Quiz Attempt Schemas
class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str


class QuizAttemptStart(BaseModel):
    quiz_id: int


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float
    total_questions: int
    correct_answers: int
    started_at: datetime
    completed_at: Optional[datetime]
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)


class QuizSubmission(BaseModel):
    attempt_id: int
    answers: List[AnswerSubmit]


class QuizResultResponse(BaseModel):
    attempt_id: int
    quiz_title: str
    score: float
    total_marks: float
    percentage: float
    correct_answers: int
    total_questions: int
    completed_at: datetime
    answers: List[dict] = []

    model_config = ConfigDict(from_attributes=True)
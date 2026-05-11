from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from app.database.connection import get_db
from app.schemas.quiz import (
    QuizCreate, QuizResponse, QuizUpdate, QuizDetailResponse,
    QuizGenerationRequest, QuizGenerationResponse,
    QuizAttemptStart, QuizAttemptResponse, QuizSubmission,
    QuizResultResponse, QuestionCreate, QuestionResponse
)
# 🔁 CHANGED: Import unified generator instead of Ollama-specific
from app.services.ai_quiz_generator import get_ai_generator
from app.models.quiz import Quiz, Question, QuizAttempt, Answer, QuestionType
from app.models.content import Content
from app.models.users import User
from app.core.security import decode_token

router = APIRouter(prefix="/quizzes", tags=["Quiz Management"])


async def get_current_user_from_token(authorization: str, db: AsyncSession) -> User:
    """Helper to get current user from token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# ========== AI/CSV Quiz Generation ==========

@router.post("/generate", response_model=QuizGenerationResponse)
async def generate_quiz_ai(
    request: QuizGenerationRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """Generate quiz from content using AI → CSV fallback"""
    
    user = await get_current_user_from_token(authorization, db)
    
    # Get content
    result = await db.execute(select(Content).where(Content.id == request.content_id))
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if not content.text_content:
        raise HTTPException(status_code=400, detail="No text content available")
    
    # 🔁 CHANGED: Use unified generator
    generator = get_ai_generator()
    
    try:
        # ✅ Auto-fallback: Tries AI first, falls back to CSV if AI fails/unavailable
        generated_questions = await generator.generate_quiz(
            content_text=content.text_content,
            num_questions=request.num_questions,
            question_types=request.question_types,
            difficulty=request.difficulty,
            use_csv_fallback=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )
    
    if not generated_questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No valid questions were generated"
        )
    
    # Detect generation method for response message
    is_csv_fallback = not generator.api_key or len(content.text_content) < 50
    generation_msg = "Quiz generated successfully via CSV fallback" if is_csv_fallback else "Quiz generated successfully with AI"
    
    # Create quiz
    quiz = Quiz(
        title=f"Quiz: {content.title}",
        description=f"{'CSV' if is_csv_fallback else 'AI'}-generated from {content.title}",
        content_id=content.id,
        created_by=user.id,
        is_ai_generated=not is_csv_fallback,
        total_marks=len(generated_questions)
    )
    
    db.add(quiz)
    await db.flush()
    
    # Create questions
    for idx, q_data in enumerate(generated_questions):
        question = Question(
            quiz_id=quiz.id,
            question_text=q_data['question_text'],
            question_type=QuestionType(q_data['question_type']),
            marks=1,
            options=q_data.get('options'),
            correct_answer=q_data['correct_answer'],
            explanation=q_data.get('explanation'),
            order_index=idx
        )
        db.add(question)
    
    await db.commit()
    await db.refresh(quiz)
    
    return QuizGenerationResponse(
        quiz_id=quiz.id,
        title=quiz.title,
        questions_generated=len(generated_questions),
        message=generation_msg
    )


# ========== Quiz Retrieval ==========

@router.get("/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz_detail(
    quiz_id: int,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """Get quiz with questions"""
    user = await get_current_user_from_token(authorization, db)
    
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions_query = select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_index)
    questions_result = await db.execute(questions_query)
    questions = questions_result.scalars().all()
    
    quiz_detail = QuizDetailResponse.model_validate(quiz)
    
    if user.is_admin or quiz.created_by == user.id:
        quiz_detail.questions = [QuestionResponse.model_validate(q) for q in questions]
    else:
        from app.schemas.quiz import QuestionWithoutAnswer
        quiz_detail.questions = [QuestionWithoutAnswer.model_validate(q) for q in questions]
    
    return quiz_detail


# ========== Quiz Attempts ==========

@router.post("/attempts/start", response_model=QuizAttemptResponse)
async def start_quiz_attempt(
    attempt_data: QuizAttemptStart,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """Start a quiz attempt"""
    user = await get_current_user_from_token(authorization, db)
    
    result = await db.execute(select(Quiz).where(Quiz.id == attempt_data.quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    if not quiz.is_active:
        raise HTTPException(status_code=400, detail="Quiz is not active")
    
    existing = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.quiz_id == quiz.id,
            QuizAttempt.user_id == user.id,
            QuizAttempt.is_completed == True
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Quiz already completed")
    
    count_result = await db.execute(
        select(func.count(Question.id)).where(Question.quiz_id == quiz.id)
    )
    question_count = count_result.scalar() or 0
    
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=user.id,
        total_questions=question_count,
        is_completed=False
    )
    
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    
    return QuizAttemptResponse.model_validate(attempt)


@router.post("/attempts/submit", response_model=QuizResultResponse)
async def submit_quiz_attempt(
    submission: QuizSubmission,
    authorization: str = Header(...),  # ✅ FIXED: Was incorrectly using Depends(lambda x: x)
    db: AsyncSession = Depends(get_db)
):
    """Submit quiz answers and get results"""
    user = await get_current_user_from_token(authorization, db)
    
    result = await db.execute(
        select(QuizAttempt).where(QuizAttempt.id == submission.attempt_id)
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this attempt"
        )
    
    if attempt.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attempt has already been submitted"
        )
    
    correct_count = 0
    total_marks = 0.0
    marks_obtained = 0.0
    
    for answer_data in submission.answers:
        q_result = await db.execute(
            select(Question).where(Question.id == answer_data.question_id)
        )
        question = q_result.scalar_one_or_none()
        
        if not question:
            continue
        
        is_correct = False
        marks = 0.0
        
        if question.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE):
            is_correct = answer_data.answer_text.strip().lower() == question.correct_answer.strip().lower()
        elif question.question_type == QuestionType.SHORT_ANSWER:
            is_correct = answer_data.answer_text.strip().lower() in question.correct_answer.strip().lower()
        
        if is_correct:
            correct_count += 1
            marks = question.marks
            marks_obtained += marks
        
        total_marks += question.marks
        
        answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            answer_text=answer_data.answer_text,
            is_correct=is_correct,
            marks_obtained=marks
        )
        db.add(answer)
    
    attempt.score = marks_obtained
    attempt.correct_answers = correct_count
    attempt.is_completed = True
    attempt.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(attempt)
    
    return QuizResultResponse(
        attempt_id=attempt.id,
        quiz_title=attempt.quiz.title,
        score=attempt.score,
        total_marks=total_marks,
        percentage=(attempt.score / total_marks * 100) if total_marks > 0 else 0,
        correct_answers=attempt.correct_answers,
        total_questions=attempt.total_questions,
        completed_at=attempt.completed_at
    )


@router.get("/attempts/{attempt_id}", response_model=QuizResultResponse)
async def get_attempt_result(
    attempt_id: int,
    authorization: str = Header(...),  # ✅ FIXED: Was incorrectly using Depends(lambda x: x)
    db: AsyncSession = Depends(get_db)
):
    """Get quiz attempt results"""
    user = await get_current_user_from_token(authorization, db)
    
    result = await db.execute(
        select(QuizAttempt).where(QuizAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.user_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this attempt"
        )
    
    if not attempt.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz attempt not yet completed"
        )
    
    total_marks = sum(q.marks for q in attempt.quiz.questions)
    
    return QuizResultResponse(
        attempt_id=attempt.id,
        quiz_title=attempt.quiz.title,
        score=attempt.score,
        total_marks=total_marks,
        percentage=(attempt.score / total_marks * 100) if total_marks > 0 else 0,
        correct_answers=attempt.correct_answers,
        total_questions=attempt.total_questions,
        completed_at=attempt.completed_at
    )
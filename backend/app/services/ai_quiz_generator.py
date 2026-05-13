import os
import json
import csv
import httpx
from typing import List, Dict, Optional, Union
from openai import OpenAI
from app.models.quiz import QuestionType


class AIQuizGenerator:
    """
    Unified quiz generator: supports both AI (OpenAI) and manual CSV fallback.
    Use generate_quiz() as the main entry point - it auto-falls back to CSV if AI fails.
    """

    def __init__(
        self, 
        api_key: Optional[str] = None,
        csv_fallback_path: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.csv_fallback_path = csv_fallback_path or os.getenv("QUIZ_CSV_FALLBACK", "data/quiz_fallback.csv")
        self._client = None
        
        # Don't raise if no API key - allows CSV-only mode
        if not self.api_key:
            print("⚠️ OPENAI_API_KEY not set. CSV/manual mode only.")
    
    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("OpenAI client requested but API key not configured")
            http_client = httpx.Client(trust_env=False, timeout=60.0)
            self._client = OpenAI(api_key=self.api_key, http_client=http_client)
        return self._client
    
    # ─────────────────────────────────────────────────────────────
    # MAIN ENTRY POINT: Auto-fallback (AI → CSV)
    # ─────────────────────────────────────────────────────────────
    async def generate_quiz(
        self,
        content_text: Optional[str] = None,
        num_questions: int = 10,
        question_types: Optional[List[QuestionType]] = None,
        difficulty: str = "medium",
        use_csv_fallback: bool = True,
        csv_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate quiz questions. Tries AI first, falls back to CSV if enabled.
        
        Args:
            content_text: Learning content for AI generation (ignored for CSV)
            num_questions: Target number of questions (CSV may return fewer)
            question_types: Allowed question types
            difficulty: Difficulty level (AI only)
            use_csv_fallback: If True, fall back to CSV when AI fails
            csv_path: Override default CSV path
        """
        # Try AI generation first (if content provided and API key exists)
        if content_text and self.api_key:
            try:
                return await self.generate_quiz_from_content(
                    content_text=content_text,
                    num_questions=num_questions,
                    question_types=question_types,
                    difficulty=difficulty
                )
            except Exception as e:
                print(f"⚠️ AI generation failed: {type(e).__name__}: {e}")
                if not use_csv_fallback:
                    raise
        
        # Fallback to CSV/manual
        path = csv_path or self.csv_fallback_path
        if os.path.exists(path):
            print(f"✓ Falling back to CSV: {path}")
            return self.generate_quiz_from_csv(path, question_types=question_types)
        
        raise RuntimeError(
            f"Quiz generation failed: AI unavailable and CSV not found at '{path}'. "
            "Set QUIZ_CSV_FALLBACK env var or provide csv_path."
        )
    
    # ─────────────────────────────────────────────────────────────
    # AI GENERATION (Original logic, now private-ish)
    # ─────────────────────────────────────────────────────────────
    async def generate_quiz_from_content(
        self,
        content_text: str,
        num_questions: int = 10,
        question_types: Optional[List[QuestionType]] = None,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """Generate quiz questions from learning content using OpenAI"""
        if not self.api_key:
            raise RuntimeError("OpenAI API key required for AI generation")
            
        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]
        
        type_strings = [qt.value for qt in question_types]
        
        if len(content_text) < 50:
            raise ValueError("Content too short to generate meaningful questions")
        
        prompt = self._create_generation_prompt(
            content=content_text,
            num_questions=num_questions,
            question_types=type_strings,
            difficulty=difficulty
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an educational AI assistant that creates high-quality quiz questions from learning content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            questions_json = response.choices[0].message.content
            questions = json.loads(questions_json)
            validated_questions = self._validate_questions(questions)
            
            if not validated_questions:
                raise ValueError("No valid questions were generated from the content")
            
            return validated_questions
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            print(f"AI Generation Error: {type(e).__name__}: {str(e)}")
            raise
    
    # ─────────────────────────────────────────────────────────────
    # CSV/MANUAL GENERATION (New method)
    # ─────────────────────────────────────────────────────────────
    def generate_quiz_from_csv(
        self, 
        csv_path: str, 
        question_types: Optional[List[QuestionType]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate quiz questions from a CSV file.
        
        Expected CSV columns:
          - question_text (required)
          - question_type (optional, default: multiple_choice)
          - options (optional, comma-separated; required for multiple_choice)
          - correct_answer (required)
          - explanation (optional)
        
        Args:
            csv_path: Path to the CSV file
            question_types: Filter to only include these types (None = all)
            limit: Max questions to return (None = all)
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        allowed_types = [qt.value for qt in (question_types or QuestionType)]
        questions = []
        
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    question = self._parse_csv_row(row)
                    
                    # Filter by question type
                    if question["question_type"] not in allowed_types:
                        continue
                        
                    questions.append(question)
                    if limit and len(questions) >= limit:
                        break
                        
                except ValueError as e:
                    print(f"⚠️ Skipping CSV row {row_num}: {e}")
                    continue

        return self._validate_questions(questions)
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Dict:
        """Parse a single CSV row into a question dict"""
        question_text = row.get("question_text", "").strip()
        if not question_text:
            raise ValueError("Missing question_text")

        question_type = row.get("question_type", "multiple_choice").strip().lower()
        valid_types = [qt.value for qt in QuestionType]
        if question_type not in valid_types:
            question_type = "multiple_choice"

        # Parse options: handle quoted comma-separated values
        options_raw = row.get("options", "")
        if options_raw:
            # csv.reader handles quoted fields correctly
            options = next(csv.reader([options_raw]))
            options = [opt.strip() for opt in options if opt.strip()]
        else:
            options = []

        correct_answer = row.get("correct_answer", "").strip()
        if not correct_answer:
            raise ValueError("Missing correct_answer")
            
        explanation = row.get("explanation", "").strip()

        return {
            "question_text": question_text,
            "question_type": question_type,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": explanation
        }
    
    # ─────────────────────────────────────────────────────────────
    # SHARED VALIDATION (Used by both AI and CSV)
    # ─────────────────────────────────────────────────────────────
    def _validate_questions(self, questions: List[Dict]) -> List[Dict]:
        """Validate and normalize questions from any source"""
        validated = []
        valid_types = [qt.value for qt in QuestionType]

        for q in questions:
            # Ensure required fields
            if not all(k in q for k in ['question_text', 'question_type', 'correct_answer']):
                continue
            
            # Normalize question type
            if q['question_type'] not in valid_types:
                q['question_type'] = 'multiple_choice'
            
            # Handle true_false type
            if q['question_type'] == 'true_false':
                q['options'] = ['True', 'False']
                q['correct_answer'] = 'True' if q['correct_answer'].lower() == 'true' else 'False'
            
            # Handle multiple_choice type
            elif q['question_type'] == 'multiple_choice':
                if not q.get('options') or len(q['options']) < 2:
                    continue  # Skip invalid MC questions
                # Normalize correct answer to match exact option casing
                matched = next(
                    (opt for opt in q['options'] if opt.lower() == q['correct_answer'].lower()), 
                    None
                )
                q['correct_answer'] = matched or q['options'][0]
            
            # Ensure explanation exists (optional but nice)
            q.setdefault('explanation', '')
            
            validated.append(q)

        return validated
    
    def _create_generation_prompt(
        self,
        content: str,
        num_questions: int,
        question_types: List[str],
        difficulty: str
    ) -> str:
        """Create the prompt for OpenAI (unchanged)"""
        truncated_content = content[:15000]
        
        return f"""
        Generate {num_questions} quiz questions based on the following educational content.
        
        Content:
        {truncated_content}
        
        Requirements:
        - Question types: {', '.join(question_types)}
        - Difficulty level: {difficulty}
        - For multiple choice questions, provide 4 options (A, B, C, D)
        - Include the correct answer for each question
        - Provide a brief explanation for each answer
        
        Format the response as a JSON array with this structure:
        [
            {{
                "question_text": "The question text here",
                "question_type": "multiple_choice",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option B",
                "explanation": "Explanation why this is correct"
            }}
        ]
        
        Ensure questions are clear, unambiguous, and directly related to the content.
        """


# ─────────────────────────────────────────────────────────────
# Lazy singleton getter (unchanged)
# ─────────────────────────────────────────────────────────────
def get_ai_generator(csv_fallback_path: Optional[str] = None) -> AIQuizGenerator:
    """Get or create the AIQuizGenerator singleton"""
    if not hasattr(get_ai_generator, "_instance"):
        get_ai_generator._instance = AIQuizGenerator(csv_fallback_path=csv_fallback_path)
    return get_ai_generator._instance
"""Domain data classes used across the application (no ORM, pure dataclasses)."""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum, auto


class DocumentType(Enum):
    PDF   = "pdf"
    IMAGE = "image"
    TEXT  = "text"


class QuizDifficulty(Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


class QuizFocus(Enum):
    MEMORIZATION  = "memorization"
    UNDERSTANDING = "understanding"
    APPLICATION   = "application"


@dataclass
class Document:
    id: Optional[int]
    workspace_id: int
    name: str
    doc_type: DocumentType
    file_path: Optional[str]
    content: Optional[str]       # for text notes
    page_count: int = 0
    current_page: int = 1
    zoom_level: int = 125
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Workspace:
    id: Optional[int]
    name: str
    active_document_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuizConfig:
    workspace_id: int
    document_id: int
    num_questions: int = 5
    difficulty: QuizDifficulty = QuizDifficulty.MEDIUM
    focus: QuizFocus = QuizFocus.UNDERSTANDING
    page_range: Optional[tuple] = None   # (start, end) or None = full doc


@dataclass
class QuizQuestion:
    id: Optional[int]
    quiz_id: int
    number: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str          # "A" | "B" | "C" | "D"
    explanation: str
    source_page: Optional[int]


@dataclass
class QuizAttempt:
    id: Optional[int]
    workspace_id: int
    document_id: int
    config: QuizConfig
    questions: List[QuizQuestion] = field(default_factory=list)
    answers: dict = field(default_factory=dict)  # {question_number: chosen_option}
    score: Optional[int] = None
    completed_at: Optional[datetime] = None

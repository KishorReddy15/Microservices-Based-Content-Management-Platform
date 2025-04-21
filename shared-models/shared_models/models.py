from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

# Common enums
class ContentType(str, Enum):
    TUTORIAL = "tutorial"
    ARTICLE = "article"
    VIDEO = "video"
    DOCUMENT = "document"
    OTHER = "other"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    CODING = "coding"

# Base models
class BaseDBModel(BaseModel):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# User models (for integration with external user service)
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase, BaseDBModel):
    is_active: bool = True
    is_admin: bool = False

# Content models
class ContentBase(BaseModel):
    title: str
    content: str
    type: ContentType = ContentType.ARTICLE

class ContentCreate(ContentBase):
    pass

class Content(ContentBase, BaseDBModel):
    pass

# Assignment models
class AssignmentBase(BaseModel):
    title: str
    description: str
    due_date: datetime
    is_published: bool = False

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase, BaseDBModel):
    pass

# Submission models
class SubmissionBase(BaseModel):
    assignment_id: str
    student_id: str
    content: str
    file_url: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    pass

class Submission(SubmissionBase, BaseDBModel):
    pass

# Quiz models
class QuestionBase(BaseModel):
    type: QuestionType
    text: str
    points: float = 1.0
    options: Optional[List[str]] = None
    correct_answer: Optional[Union[int, str]] = None
    code_template: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    pass

class QuizBase(BaseModel):
    title: str
    description: str
    questions: List[Question]
    duration_minutes: int = 60
    passing_score: Optional[float] = None
    is_published: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class QuizCreate(QuizBase):
    pass

class Quiz(QuizBase, BaseDBModel):
    pass

# Forum models
class TopicBase(BaseModel):
    title: str
    description: str

class TopicCreate(TopicBase):
    pass

class PostBase(BaseModel):
    content: str
    author: str
    topic_id: Optional[str] = None

class PostCreate(PostBase):
    pass

class Post(PostBase, BaseDBModel):
    pass

class Topic(TopicBase, BaseDBModel):
    posts: List[Post] = []

# Grading models
class GradeBase(BaseModel):
    submission_id: str
    grader_id: str
    score: float
    feedback: Optional[str] = None

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase, BaseDBModel):
    pass

# Notification models (for integration with external notification service)
class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationBase(BaseModel):
    recipient_id: str
    type: NotificationType
    subject: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase, BaseDBModel):
    status: str = "pending"

# Payment models (for integration with external payment service)
class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentBase(BaseModel):
    user_id: str
    amount: float
    currency: str = "USD"
    description: str
    metadata: Optional[Dict[str, Any]] = None

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase, BaseDBModel):
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str] = None

# Analytics models (for integration with external analytics service)
class UserActivity(BaseModel):
    user_id: str
    activity_type: str
    resource_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsReport(BaseModel):
    report_type: str
    start_date: datetime
    end_date: datetime
    data: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Integration models
class ServiceRequest(BaseModel):
    service: str
    endpoint: str
    method: str = "GET"
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None

class ServiceResponse(BaseModel):
    status_code: int
    content: Any
    headers: Dict[str, str] = Field(default_factory=dict)

class IntegratedUserDashboard(BaseModel):
    user: Dict[str, Any]
    academic: Dict[str, Any]
    analytics: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

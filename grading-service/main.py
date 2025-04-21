from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import os
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pymongo import MongoClient
import json
import time
import requests

# Import the feedback client
from feedback_integration.client import FeedbackClient

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/content_management")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client.grading

# Student Feedback configuration
STUDENT_FEEDBACK_URL = os.getenv("STUDENT_FEEDBACK_URL", "http://student-feedback-service:8000")
feedback_client = FeedbackClient(STUDENT_FEEDBACK_URL)

# Database models
class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    max_points = Column(Integer, default=100)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, nullable=False)
    score = Column(Float)
    feedback = Column(String(500))
    rubric_scores = Column(JSON)  # Store rubric scores as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignment = relationship("Assignment")

@app.on_event("startup")
async def startup_event():
    # Try to create tables with retries
    max_retries = 30
    retry_delay = 10

    for attempt in range(max_retries):
        db = None
        try:
            db = SessionLocal()
            # First verify that the assignments table exists
            db.execute("SELECT 1 FROM assignments LIMIT 1")
            print("Successfully verified assignments table exists")

            # Create our tables if they don't exist
            Base.metadata.create_all(bind=engine)
            print("Successfully created/verified grades table")

            if db:
                db.close()
            return

        except Exception as e:
            print(f"Failed to verify/create tables (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if db:
                db.close()
            if attempt >= max_retries - 1:
                raise e
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

# Remove Assignment model definition and continue with Pydantic models
class RubricItem(BaseModel):
    criterion: str
    points: float
    description: str

class Rubric(BaseModel):
    items: List[RubricItem]
    total_points: float

class GradeCreate(BaseModel):
    assignment_id: str
    student_id: int
    score: float
    feedback: Optional[str] = None
    rubric_scores: Optional[Dict[str, float]] = None

class GradeResponse(BaseModel):
    id: int
    assignment_id: str
    student_id: int
    score: float
    feedback: Optional[str]
    rubric_scores: Optional[Dict[str, float]]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DetailedFeedback(BaseModel):
    grade_id: int
    assignment_id: str
    student_id: int
    score_breakdown: Dict[str, float]
    comments: str
    suggestions: List[str]
    submission_date: datetime

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    db = None
    try:
        # Check PostgreSQL connection
        db = SessionLocal()
        db.execute("SELECT 1")

        # Check MongoDB connection
        mongo_client.server_info()

        return {"status": "healthy", "postgresql": "connected", "mongodb": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    finally:
        if db:
            db.close()

# Routes
@app.post("/grades", response_model=GradeResponse)
async def submit_grade(grade: GradeCreate, db: Session = Depends(get_db)):
    # Store in PostgreSQL
    db_grade = Grade(**grade.dict())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)

    # Store detailed feedback in MongoDB
    mongo_feedback = {
        "grade_id": str(db_grade.id),
        "assignment_id": str(grade.assignment_id),
        "student_id": grade.student_id,
        "score_breakdown": grade.rubric_scores or {},
        "comments": grade.feedback or "",
        "suggestions": [],
        "submission_date": datetime.utcnow().isoformat()
    }
    mongo_db.feedback.insert_one(mongo_feedback)

    return db_grade

@app.get("/grades/{assignment_id}", response_model=List[GradeResponse])
async def get_grades(assignment_id: str, db: Session = Depends(get_db)):
    return db.query(Grade).filter(Grade.assignment_id == assignment_id).all()

@app.get("/grades/{assignment_id}/detailed/{student_id}")
async def get_detailed_grade(assignment_id: str, student_id: int, db: Session = Depends(get_db)):
    # Get basic grade from PostgreSQL
    grade = db.query(Grade).filter(
        Grade.assignment_id == assignment_id,
        Grade.student_id == student_id
    ).first()

    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")

    # Get detailed feedback from MongoDB
    mongo_feedback = mongo_db.feedback.find_one({
        "assignment_id": assignment_id,
        "student_id": student_id
    })

    if mongo_feedback:
        del mongo_feedback['_id']  # Remove MongoDB's _id field
        return {
            "basic_grade": GradeResponse.from_orm(grade).dict(),
            "detailed_feedback": mongo_feedback
        }
    else:
        return {
            "basic_grade": GradeResponse.from_orm(grade).dict(),
            "detailed_feedback": None
        }

@app.post("/grades/{grade_id}/feedback")
async def add_detailed_feedback(
    grade_id: int,
    feedback: DetailedFeedback,
    db: Session = Depends(get_db)
):
    # Update MongoDB with detailed feedback
    mongo_feedback = {
        "grade_id": str(grade_id),
        "assignment_id": str(feedback.assignment_id),
        "student_id": feedback.student_id,
        "score_breakdown": feedback.score_breakdown,
        "comments": feedback.comments,
        "suggestions": feedback.suggestions,
        "submission_date": feedback.submission_date.isoformat()
    }

    mongo_db.feedback.update_one(
        {"grade_id": str(grade_id)},
        {"$set": mongo_feedback},
        upsert=True
    )

    return {"message": "Detailed feedback added successfully"}

@app.get("/grades/{assignment_id}/statistics")
async def get_assignment_statistics(assignment_id: str, db: Session = Depends(get_db)):
    grades = db.query(Grade).filter(Grade.assignment_id == assignment_id).all()

    if not grades:
        raise HTTPException(status_code=404, detail="No grades found for this assignment")

    scores = [grade.score for grade in grades]
    statistics = {
        "average": sum(scores) / len(scores),
        "highest": max(scores),
        "lowest": min(scores),
        "total_submissions": len(scores)
    }

    return statistics

# Student Feedback Integration Endpoints

@app.get("/grades/{assignment_id}/student/{student_id}/with-feedback")
async def get_grade_with_feedback(assignment_id: str, student_id: int, db: Session = Depends(get_db)):
    """Get a grade with student performance feedback"""
    # Get the grade from the database
    grade = db.query(Grade).filter(
        Grade.assignment_id == assignment_id,
        Grade.student_id == student_id
    ).first()

    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")

    # Get detailed feedback from MongoDB
    mongo_feedback = mongo_db.feedback.find_one({
        "assignment_id": assignment_id,
        "student_id": student_id
    })

    # Get student performance feedback from the student feedback service
    try:
        performance_feedbacks = feedback_client.get_student_feedbacks(student_id)
    except Exception as e:
        performance_feedbacks = []
        print(f"Error getting student performance feedback: {str(e)}")

    # Filter feedbacks related to this assignment if assignment_id is present
    assignment_feedbacks = []
    for feedback in performance_feedbacks:
        if feedback.get("assignment_id") == assignment_id:
            assignment_feedbacks.append(feedback)

    # Prepare the response
    response = {
        "grade": GradeResponse.from_orm(grade).dict(),
        "detailed_feedback": mongo_feedback if mongo_feedback else None,
        "performance_feedbacks": assignment_feedbacks if assignment_feedbacks else performance_feedbacks
    }

    # Remove MongoDB's _id field if present
    if response["detailed_feedback"] and "_id" in response["detailed_feedback"]:
        del response["detailed_feedback"]["_id"]

    return response

@app.post("/grades/{assignment_id}/student/{student_id}/performance-feedback")
async def create_performance_feedback(
    assignment_id: str,
    student_id: int,
    feedback_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create performance feedback for a student's assignment"""
    # Check if the grade exists
    grade = db.query(Grade).filter(
        Grade.assignment_id == assignment_id,
        Grade.student_id == student_id
    ).first()

    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")

    # Extract feedback data
    mentor_id = feedback_data.get("mentor_id")
    if not mentor_id:
        raise HTTPException(status_code=400, detail="mentor_id is required")

    feedback_text = feedback_data.get("feedback_text", "")
    performance_areas = feedback_data.get("performance_areas", [])
    improvement_suggestions = feedback_data.get("improvement_suggestions", [])
    strengths = feedback_data.get("strengths", [])

    # Create the feedback in the background to avoid blocking the response
    def create_feedback_task():
        try:
            feedback = feedback_client.create_feedback(
                student_id=student_id,
                mentor_id=mentor_id,
                assignment_id=assignment_id,
                grade_id=str(grade.id),
                feedback_text=feedback_text,
                performance_areas=performance_areas,
                improvement_suggestions=improvement_suggestions,
                strengths=strengths
            )
            print(f"Created performance feedback: {feedback}")
            return feedback
        except Exception as e:
            print(f"Error creating performance feedback: {str(e)}")
            return None

    # Add the task to the background tasks
    background_tasks.add_task(create_feedback_task)

    return {"status": "success", "message": "Performance feedback creation initiated"}

@app.get("/students/{student_id}/performance-feedbacks")
async def get_student_performance_feedbacks(student_id: int):
    """Get all performance feedbacks for a student"""
    try:
        feedbacks = feedback_client.get_student_feedbacks(student_id)
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting student performance feedbacks: {str(e)}")
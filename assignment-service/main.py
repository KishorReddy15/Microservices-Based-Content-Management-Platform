from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import shutil
from pathlib import Path
import time

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/content_management")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# File upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Database models
class AssignmentDB(Base):
    __tablename__ = "assignments"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Boolean, default=True)

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String, ForeignKey("assignments.id"))
    student_id = Column(Integer)
    file_path = Column(String(255))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    is_late = Column(Boolean, default=False)

# Create tables
Base.metadata.create_all(bind=engine)
print("Successfully created database tables")

# Check if is_published column exists in assignments table
def check_and_add_is_published_column():
    try:
        with engine.connect() as connection:
            # Check if the column exists
            result = connection.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assignments' AND column_name='is_published'")
            if result.rowcount == 0:
                # Add the column if it doesn't exist
                connection.execute("ALTER TABLE assignments ADD COLUMN is_published BOOLEAN DEFAULT TRUE")
                print("Added is_published column to assignments table")
    except Exception as e:
        print(f"Error checking/adding is_published column: {e}")

# Run the column check
check_and_add_is_published_column()

# Pydantic models
class AssignmentBase(BaseModel):
    title: str
    description: str
    due_date: datetime

class AssignmentResponse(AssignmentBase):
    id: str
    created_at: datetime
    is_published: bool
    model_config = ConfigDict(from_attributes=True)

class SubmissionResponse(BaseModel):
    id: int
    assignment_id: str
    student_id: int
    file_path: str
    submitted_at: datetime
    is_late: bool
    model_config = ConfigDict(from_attributes=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    # Try to create tables with retries
    max_retries = 10
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Successfully created database tables")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Failed to create tables (attempt {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(retry_delay)
            else:
                print("Failed to create tables after all retries")
                raise e

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Create assignment
@app.post("/assignments/", response_model=AssignmentResponse)
async def create_assignment(assignment: AssignmentBase, db: Session = Depends(get_db)):
    db_assignment = AssignmentDB(
        id=os.urandom(8).hex(),
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

# Get all assignments
@app.get("/assignments/", response_model=List[AssignmentResponse])
async def get_all_assignments(db: Session = Depends(get_db)):
    assignments = db.query(AssignmentDB).all()
    return assignments

# Get assignment by ID
@app.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: str, db: Session = Depends(get_db)):
    assignment = db.query(AssignmentDB).filter(AssignmentDB.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

# Update assignment
@app.put("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(assignment_id: str, assignment: AssignmentBase, db: Session = Depends(get_db)):
    db_assignment = db.query(AssignmentDB).filter(AssignmentDB.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db_assignment.title = assignment.title
    db_assignment.description = assignment.description
    db_assignment.due_date = assignment.due_date

    db.commit()
    db.refresh(db_assignment)
    return db_assignment

# Delete assignment
@app.delete("/assignments/{assignment_id}")
async def delete_assignment(assignment_id: str, db: Session = Depends(get_db)):
    db_assignment = db.query(AssignmentDB).filter(AssignmentDB.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(db_assignment)
    db.commit()
    return {"status": "deleted", "id": assignment_id}

@app.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: str,
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if assignment exists and is published
    assignment = db.query(AssignmentDB).filter(AssignmentDB.id == assignment_id).first()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if not assignment.is_published:
        raise HTTPException(status_code=400, detail="Assignment is not published")

    # Check if submission is late
    is_late = assignment.due_date and datetime.utcnow() > assignment.due_date

    # Save file
    file_path = UPLOAD_DIR / f"assignment_{assignment_id}_student_{student_id}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create submission record
    submission = Submission(
        assignment_id=assignment_id,
        student_id=student_id,
        file_path=str(file_path),
        is_late=is_late
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {"message": "Assignment submitted successfully", "submission_id": submission.id}

@app.get("/assignments/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def get_submissions(assignment_id: str, db: Session = Depends(get_db)):
    return db.query(Submission).filter(Submission.assignment_id == assignment_id).all()
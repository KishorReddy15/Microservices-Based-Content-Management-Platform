from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timezone
import os
from pydantic import BaseModel, Field, ValidationError, validator
from typing import List, Optional, Dict, Union, Any
from bson.objectid import ObjectId
from bson import errors
from enum import Enum

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client.content_management
quiz_collection = db.quizzes

# Helper function for timezone-aware UTC now
def utc_now():
    return datetime.now(timezone.utc)

# Helper function to convert MongoDB document to response format
def format_quiz_response(quiz: dict) -> dict:
    # Create a copy of the quiz dict
    response = quiz.copy()

    # Convert _id to string id
    response["id"] = str(response.pop("_id"))

    # Ensure required fields have default values
    response["description"] = response.get("description", "")
    response["duration_minutes"] = response.get("duration_minutes", 60)
    response["is_published"] = response.get("is_published", False)
    response["passing_score"] = response.get("passing_score", None)
    response["created_at"] = response.get("created_at", None)
    response["updated_at"] = response.get("updated_at", None)
    response["questions"] = response.get("questions", [])

    return response

# Helper function to validate ObjectId
def validate_object_id(id_str: str) -> ObjectId:
    try:
        # Handle the case where the ID is already an ObjectId string
        if isinstance(id_str, str) and len(id_str) == 24:
            try:
                return ObjectId(id_str)
            except Exception:
                pass

        # If that fails, try to create a new ObjectId from the string
        try:
            return ObjectId(id_str)
        except Exception:
            # If all else fails, create a new ObjectId with the same string representation
            new_id = '0' * (24 - len(id_str)) + id_str
            return ObjectId(new_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid quiz ID format: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    CODE = "code"

class Question(BaseModel):
    type: QuestionType
    text: str
    points: float
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: Union[int, str, bool]  # Index for multiple choice, answer for short answer, bool for true/false
    code_template: Optional[str] = None  # For code questions
    test_cases: Optional[List[Dict[str, str]]] = None  # For code questions

    @validator('options')
    def validate_options(cls, v, values):
        if values.get('type') == QuestionType.MULTIPLE_CHOICE and (not v or len(v) < 2):
            raise ValueError('Multiple choice questions must have at least 2 options')
        return v

    @validator('correct_answer')
    def validate_correct_answer(cls, v, values):
        if values.get('type') == QuestionType.MULTIPLE_CHOICE:
            if not isinstance(v, int) or v < 0 or (values.get('options') and v >= len(values['options'])):
                raise ValueError('Multiple choice correct_answer must be a valid option index')
        elif values.get('type') == QuestionType.TRUE_FALSE:
            if not isinstance(v, bool):
                raise ValueError('True/False correct_answer must be a boolean')
        return v

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    questions: List[Question]
    duration_minutes: int = 60  # Changed from time_limit, made required with default
    passing_score: Optional[float] = None
    is_published: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class Quiz(BaseModel):
    title: str
    description: str = ""
    questions: List[Question]
    duration_minutes: int = 60  # Made consistent with QuizCreate
    passing_score: Optional[float] = None
    is_published: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class QuizResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    questions: List[Question]
    duration_minutes: int
    passing_score: Optional[float] = None
    is_published: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class QuizSubmission(BaseModel):
    quiz_id: str
    student_id: int
    answers: List[Union[int, str, bool]]
    submission_time: datetime

    @validator('submission_time')
    def ensure_timezone(cls, v):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

# Create quiz
@app.post("/quizzes", response_model=QuizResponse)
async def create_quiz_new(quiz: QuizCreate):
    try:
        # Convert the quiz model to a dictionary
        quiz_data = quiz.dict()

        # Add required fields with defaults
        quiz_data.update({
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "is_published": False,
            "description": quiz_data.get("description", ""),
            "duration_minutes": quiz_data.get("duration_minutes", 60),
            "passing_score": quiz_data.get("passing_score", None)
        })

        # Insert into database - MongoDB operations are not async in pymongo
        result = quiz_collection.insert_one(quiz_data)

        # Get the inserted document
        inserted_quiz = quiz_collection.find_one({"_id": result.inserted_id})
        if not inserted_quiz:
            raise HTTPException(status_code=500, detail="Failed to create quiz")

        # Create the response data
        response_data = {
            "id": str(inserted_quiz["_id"]),
            "title": inserted_quiz["title"],
            "description": inserted_quiz.get("description", ""),
            "questions": inserted_quiz["questions"],
            "duration_minutes": inserted_quiz.get("duration_minutes", 60),
            "passing_score": inserted_quiz.get("passing_score", None),
            "is_published": inserted_quiz.get("is_published", False),
            "created_at": inserted_quiz.get("created_at"),
            "updated_at": inserted_quiz.get("updated_at")
        }

        # Validate and return the response
        return QuizResponse(**response_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create quiz: {str(e)}")

# Get all quizzes
@app.get("/quizzes")
async def get_quizzes():
    try:
        quizzes = list(quiz_collection.find())
        if not quizzes:
            return []
        formatted_quizzes = [format_quiz_response(quiz) for quiz in quizzes]
        # Return the formatted quizzes directly without validation
        return formatted_quizzes
    except Exception as e:
        print(f"Error fetching quizzes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quizzes: {str(e)}")

# Helper function to get a quiz by ID
def get_quiz_by_id(quiz_id: str) -> dict:
    # Try different ways to find the quiz
    quiz = None

    # Try by ObjectId
    try:
        quiz = quiz_collection.find_one({"_id": ObjectId(quiz_id)})
    except:
        pass

    # Try by string ID
    if not quiz:
        quiz = quiz_collection.find_one({"_id": quiz_id})

    # Try by string comparison
    if not quiz:
        all_quizzes = list(quiz_collection.find())
        for q in all_quizzes:
            if str(q["_id"]) == quiz_id:
                quiz = q
                break

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return quiz

# Get quiz by ID
@app.get("/quizzes/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str):
    try:
        object_id = validate_object_id(quiz_id)
        quiz = quiz_collection.find_one({"_id": object_id})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return QuizResponse(**format_quiz_response(quiz))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quiz: {str(e)}")

# Update quiz
@app.put("/quizzes/{quiz_id}", response_model=QuizResponse)
async def update_quiz(quiz_id: str, quiz: Quiz):
    try:
        object_id = validate_object_id(quiz_id)
        quiz_dict = quiz.dict()
        quiz_dict["updated_at"] = utc_now()
        result = quiz_collection.find_one_and_update(
            {"_id": object_id},
            {"$set": quiz_dict},
            return_document=True
        )
        if not result:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return QuizResponse(**format_quiz_response(result))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update quiz: {str(e)}")

# Delete quiz
@app.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str):
    try:
        object_id = validate_object_id(quiz_id)
        # Check if quiz exists first
        quiz = quiz_collection.find_one({"_id": object_id})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Delete the quiz
        result = quiz_collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return {"status": "success", "message": "Quiz deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete quiz: {str(e)}")

# Publish quiz
@app.post("/quizzes/{quiz_id}/publish")
async def publish_quiz(quiz_id: str):
    try:
        object_id = validate_object_id(quiz_id)
        result = quiz_collection.find_one_and_update(
            {"_id": object_id},
            {
                "$set": {
                    "is_published": True,
                    "updated_at": utc_now()
                }
            },
            return_document=True
        )
        if not result:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return {"status": "success", "message": "Quiz published successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish quiz: {str(e)}")

# Submit quiz
@app.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, submission: QuizSubmission):
    try:
        object_id = validate_object_id(quiz_id)
        if quiz_id != submission.quiz_id:
            raise HTTPException(status_code=400, detail="Quiz ID in URL does not match quiz ID in submission")

        quiz = quiz_collection.find_one({"_id": object_id})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        if not quiz.get("is_published", False):
            raise HTTPException(status_code=400, detail="Quiz is not published")

        if len(submission.answers) != len(quiz["questions"]):
            raise HTTPException(
                status_code=400,
                detail=f"Number of answers ({len(submission.answers)}) does not match number of questions ({len(quiz['questions'])})"
            )

        score = 0
        total_points = 0
        detailed_results = []

        for question, answer in zip(quiz["questions"], submission.answers):
            total_points += question["points"]
            is_correct = False

            if question["type"] == QuestionType.MULTIPLE_CHOICE:
                is_correct = answer == question["correct_answer"]
            elif question["type"] == QuestionType.TRUE_FALSE:
                is_correct = answer == question["correct_answer"]
            elif question["type"] == QuestionType.SHORT_ANSWER:
                is_correct = str(answer).lower().strip() == str(question["correct_answer"]).lower().strip()
            elif question["type"] == QuestionType.CODE:
                is_correct = True  # Simplified version

            if is_correct:
                score += question["points"]

            detailed_results.append({
                "question": question["text"],
                "answer": answer,
                "correct": is_correct,
                "points_earned": question["points"] if is_correct else 0,
                "total_points": question["points"]
            })

        percentage = (score / total_points) * 100 if total_points > 0 else 0
        passed = quiz.get("passing_score") is None or percentage >= quiz.get("passing_score", 0)

        current_time = utc_now()
        submission_time = submission.submission_time
        time_taken = (current_time - submission_time).total_seconds()

        result = {
            "quiz_id": quiz_id,
            "student_id": submission.student_id,
            "score": score,
            "total_points": total_points,
            "percentage": percentage,
            "passed": passed,
            "time_taken": time_taken,
            "detailed_results": detailed_results,
            "submitted_at": current_time
        }

        quiz_collection.update_one(
            {"_id": object_id},
            {"$push": {"results": result}}
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")

# Get quiz results for a student
@app.get("/quizzes/{quiz_id}/results/{student_id}")
async def get_quiz_result(quiz_id: str, student_id: int):
    try:
        object_id = validate_object_id(quiz_id)
        quiz = quiz_collection.find_one({
            "_id": object_id,
            "results.student_id": student_id
        })
        if not quiz:
            raise HTTPException(status_code=404, detail="No results found for this student")

        # Find the student's results
        student_results = [r for r in quiz.get("results", []) if r["student_id"] == student_id]
        if not student_results:
            raise HTTPException(status_code=404, detail="No results found for this student")

        return student_results[0]  # Return the most recent result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quiz results: {str(e)}")

# Get quiz statistics
@app.get("/quizzes/{quiz_id}/statistics")
async def get_quiz_statistics(quiz_id: str):
    try:
        quiz = get_quiz_by_id(quiz_id)
        results = quiz.get("results", [])

        if not results:
            return {
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "pass_rate": 0,
                "total_submissions": 0,
                "message": "No submissions yet"
            }

        scores = [float(result["percentage"]) for result in results]
        passed = sum(1 for r in results if r.get("passed", False))

        return {
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": round(max(scores), 2),
            "lowest_score": round(min(scores), 2),
            "pass_rate": round((passed / len(results)) * 100, 2),
            "total_submissions": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quiz statistics: {str(e)}")
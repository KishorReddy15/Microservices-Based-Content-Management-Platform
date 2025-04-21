from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import uvicorn
import os

app = FastAPI()

# MongoDB setup
mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
client = MongoClient(mongodb_url)
db = client["student_performance_db"]

# Collections
users_collection = db["users"]
students_collection = db["students"]
mentors_collection = db["mentors"]
feedbacks_collection = db["feedbacks"]

# Helper to serialize ObjectId
def serialize_doc(doc):
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

# Pydantic models
class User(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str  # "student", "mentor", or "admin"
    department: Optional[str] = None
    student_id: Optional[str] = None
    mentor_id: Optional[str] = None
    admin_id: Optional[str] = None

class Student(BaseModel):
    student_id: str
    name: str
    email: EmailStr
    department: str

class Mentor(BaseModel):
    mentor_id: str
    name: str
    email: EmailStr
    department: str

class PerformanceFeedback(BaseModel):
    student_id: str
    mentor_id: str
    feedback: str
    date: datetime = datetime.utcnow()
    highlights: List[str]

# Routes

@app.get("/")
async def root():
    return {"message": "Welcome to Student Performance Feedback Service"}

# --------------------- ADMIN ---------------------

@app.post("/admin/register")
async def register_admin(user: User):
    if user.role != "admin":
        return {"message": "Only admin registration allowed here"}
    
    if users_collection.find_one({"email": user.email}):
        return {"message": "Email already registered"}
    
    users_collection.insert_one(user.model_dump())
    return {"message": "Admin registered successfully"}

@app.post("/admin/student/create")
async def create_student(student: Student):
    if students_collection.find_one({"student_id": student.student_id}):
        return {"message": "Student ID already exists"}
    
    if students_collection.find_one({"email": student.email}):
        return {"message": "Email already registered"}
    
    students_collection.insert_one(student.model_dump())
    return {"message": "Student created successfully"}

@app.post("/admin/mentor/create")
async def create_mentor(mentor: Mentor):
    if mentors_collection.find_one({"mentor_id": mentor.mentor_id}):
        return {"message": "Mentor ID already exists"}
    
    if mentors_collection.find_one({"email": mentor.email}):
        return {"message": "Email already registered"}
    
    mentors_collection.insert_one(mentor.model_dump())
    return {"message": "Mentor created successfully"}

@app.get("/admin/students")
async def list_students():
    return [serialize_doc(student) for student in students_collection.find()]

@app.get("/admin/mentors")
async def list_mentors():
    return [serialize_doc(mentor) for mentor in mentors_collection.find()]

# --------------------- MENTOR ---------------------

@app.post("/mentor/feedback/create")
async def create_feedback(feedback: PerformanceFeedback):
    student = students_collection.find_one({"student_id": feedback.student_id})
    if not student:
        return {"message": "Student not found"}
    
    mentor = mentors_collection.find_one({"mentor_id": feedback.mentor_id})
    if not mentor:
        return {"message": "Mentor not found"}
    
    feedback_dict = feedback.model_dump()
    feedback_dict["student_name"] = student["name"]
    feedback_dict["mentor_name"] = mentor["name"]
    
    feedbacks_collection.insert_one(feedback_dict)
    return {"message": "Feedback created successfully"}

@app.get("/mentor/{mentor_id}/feedbacks")
async def list_mentor_feedbacks(mentor_id: str):
    return [serialize_doc(feedback) for feedback in feedbacks_collection.find({"mentor_id": mentor_id})]

# --------------------- STUDENT ---------------------

@app.get("/student/{student_id}/feedbacks")
async def list_student_feedbacks(student_id: str):
    return [serialize_doc(feedback) for feedback in feedbacks_collection.find({"student_id": student_id})]

# --------------------- MAIN ---------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
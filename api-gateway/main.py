from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment variables
ASSIGNMENT_SERVICE_URL = os.getenv("ASSIGNMENT_SERVICE_URL")
GRADING_SERVICE_URL = os.getenv("GRADING_SERVICE_URL")
QUIZ_SERVICE_URL = os.getenv("QUIZ_SERVICE_URL")
FORUM_SERVICE_URL = os.getenv("FORUM_SERVICE_URL")
CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL")

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Check all service health endpoints
        services = {
            "assignment": ASSIGNMENT_SERVICE_URL,
            "grading": GRADING_SERVICE_URL,
            "quiz": QUIZ_SERVICE_URL,
            "forum": FORUM_SERVICE_URL,
            "content": CONTENT_SERVICE_URL
        }

        status = {"status": "healthy", "services": {}}
        for name, url in services.items():
            try:
                response = requests.get(f"{url}/health")
                status["services"][name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                status["services"][name] = "unreachable"
                status["status"] = "degraded"

        return status
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# Assignment Routes
@app.post("/assignments")
async def create_assignment(assignment: dict):
    response = requests.post(f"{ASSIGNMENT_SERVICE_URL}/assignments", json=assignment)
    return response.json()

@app.get("/assignments")
async def get_assignments():
    response = requests.get(f"{ASSIGNMENT_SERVICE_URL}/assignments")
    return response.json()

# Grading Routes
@app.post("/grades")
async def submit_grade(grade: dict):
    response = requests.post(f"{GRADING_SERVICE_URL}/grades", json=grade)
    return response.json()

@app.get("/grades/{assignment_id}")
async def get_grades(assignment_id: str):
    response = requests.get(f"{GRADING_SERVICE_URL}/grades/{assignment_id}")
    return response.json()

# Quiz Routes
@app.post("/quizzes")
async def create_quiz(quiz: dict):
    try:
        response = requests.post(f"{QUIZ_SERVICE_URL}/quizzes", json=quiz)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.get("/quizzes")
async def get_all_quizzes():
    try:
        response = requests.get(f"{QUIZ_SERVICE_URL}/quizzes")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: str):
    try:
        response = requests.get(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.put("/quizzes/{quiz_id}")
async def update_quiz(quiz_id: str, quiz: dict):
    try:
        response = requests.put(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}", json=quiz)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str):
    try:
        response = requests.delete(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.post("/quizzes/{quiz_id}/publish")
async def publish_quiz(quiz_id: str):
    try:
        response = requests.post(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/publish")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.get("/quizzes/{quiz_id}/statistics")
async def get_quiz_statistics(quiz_id: str):
    try:
        response = requests.get(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/statistics")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

# Forum Routes
@app.post("/forum/posts")
async def create_post(post: dict):
    response = requests.post(f"{FORUM_SERVICE_URL}/posts", json=post)
    return response.json()

@app.get("/forum/posts")
async def get_posts():
    response = requests.get(f"{FORUM_SERVICE_URL}/posts")
    return response.json()

@app.post("/forum/posts/{post_id}/comments")
async def add_comment(post_id: str, comment: dict):
    response = requests.post(f"{FORUM_SERVICE_URL}/posts/{post_id}/comments", json=comment)
    return response.json()

# Content Routes
@app.post("/content")
async def create_content(content: dict):
    try:
        response = requests.post(f"{CONTENT_SERVICE_URL}/content", json=content)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.get("/content")
async def get_all_content():
    try:
        response = requests.get(f"{CONTENT_SERVICE_URL}/content")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.get("/content/{content_id}")
async def get_content(content_id: str):
    try:
        response = requests.get(f"{CONTENT_SERVICE_URL}/content/{content_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.put("/content/{content_id}")
async def update_content(content_id: str, content: dict):
    try:
        response = requests.put(f"{CONTENT_SERVICE_URL}/content/{content_id}", json=content)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)

@app.delete("/content/{content_id}")
async def delete_content(content_id: str):
    try:
        response = requests.delete(f"{CONTENT_SERVICE_URL}/content/{content_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error_detail = e.response.json().get('detail', str(e))
        else:
            error_detail = str(e)
        raise HTTPException(status_code=e.response.status_code if hasattr(e, 'response') else 500, detail=error_detail)
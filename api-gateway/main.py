from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import time
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api-gateway")

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
INTEGRATION_LAYER_URL = os.getenv("INTEGRATION_LAYER_URL")
CALENDAR_SERVICE_URL = os.getenv("CALENDAR_SERVICE_URL")
STUDENT_FEEDBACK_URL = os.getenv("STUDENT_FEEDBACK_URL", "http://student-feedback-service:8000")

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

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
            "content": CONTENT_SERVICE_URL,
            "integration": INTEGRATION_LAYER_URL,
            "calendar": CALENDAR_SERVICE_URL
        }

        status = {"status": "healthy", "services": {}, "timestamp": datetime.now(timezone.utc).isoformat()}
        for name, url in services.items():
            if not url:  # Skip if URL is not configured
                continue

            try:
                response = requests.get(f"{url}/health", timeout=5.0)
                status["services"][name] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception as service_error:
                logger.warning(f"Health check failed for {name}: {str(service_error)}")
                status["services"][name] = "unreachable"
                status["status"] = "degraded"

        return status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
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

# External service routes through integration layer
@app.get("/external/{path:path}")
async def external_service_proxy(path: str, request: Request):
    if not INTEGRATION_LAYER_URL:
        raise HTTPException(status_code=503, detail="Integration layer not configured")

    try:
        # Forward the request to the integration layer
        url = f"{INTEGRATION_LAYER_URL}/external/{path}"

        # Get query parameters
        params = dict(request.query_params)

        # Forward the request
        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying to external service: {str(e)}")
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"External service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.post("/external/{path:path}")
async def external_service_proxy_post(path: str, request: Request):
    if not INTEGRATION_LAYER_URL:
        raise HTTPException(status_code=503, detail="Integration layer not configured")

    try:
        # Forward the request to the integration layer
        url = f"{INTEGRATION_LAYER_URL}/external/{path}"

        # Get the request body
        body = await request.json()

        # Forward the request
        response = requests.post(url, json=body)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying to external service: {str(e)}")
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"External service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

# Calendar Routes
@app.get("/calendar/events")
async def get_calendar_events():
    try:
        response = requests.get(f"{CALENDAR_SERVICE_URL}/api/events")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Calendar service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.get("/calendar/events/{event_id}")
async def get_calendar_event(event_id: str):
    try:
        response = requests.get(f"{CALENDAR_SERVICE_URL}/api/events/{event_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Calendar service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.post("/calendar/events")
async def create_calendar_event(event: dict):
    try:
        response = requests.post(f"{CALENDAR_SERVICE_URL}/api/events", json=event)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Calendar service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.put("/calendar/events/{event_id}")
async def update_calendar_event(event_id: str, event: dict):
    try:
        response = requests.put(f"{CALENDAR_SERVICE_URL}/api/events/{event_id}", json=event)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Calendar service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str):
    try:
        response = requests.delete(f"{CALENDAR_SERVICE_URL}/api/events/{event_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Calendar service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.get("/calendar/events/upcoming")
async def get_upcoming_calendar_events():
    try:
        response = requests.get(f"{CALENDAR_SERVICE_URL}/api/events/upcoming")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Calendar service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

# Quiz Schedule Routes
@app.post("/quizzes/{quiz_id}/schedule")
async def schedule_quiz(quiz_id: str, schedule_data: dict):
    try:
        response = requests.post(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/schedule", params=schedule_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Quiz service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.put("/quizzes/{quiz_id}/schedule")
async def update_quiz_schedule(quiz_id: str, schedule_data: dict):
    try:
        response = requests.put(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/schedule", params=schedule_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Quiz service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.delete("/quizzes/{quiz_id}/schedule")
async def cancel_quiz_schedule(quiz_id: str):
    try:
        response = requests.delete(f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/schedule")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Quiz service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.get("/quizzes/scheduled")
async def get_scheduled_quizzes():
    try:
        response = requests.get(f"{QUIZ_SERVICE_URL}/quizzes/scheduled")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Quiz service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.get("/quizzes/scheduled/upcoming")
async def get_upcoming_scheduled_quizzes():
    try:
        response = requests.get(f"{QUIZ_SERVICE_URL}/quizzes/scheduled/upcoming")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Quiz service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

# Student Feedback Routes
@app.get("/student-feedback/students/{student_id}/feedbacks")
async def get_student_feedbacks(student_id: int):
    try:
        response = requests.get(f"{STUDENT_FEEDBACK_URL}/student/{student_id}/feedbacks")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Student feedback service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.post("/student-feedback/feedbacks")
async def create_feedback(feedback: dict):
    try:
        response = requests.post(f"{STUDENT_FEEDBACK_URL}/feedbacks", json=feedback)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Student feedback service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.get("/student-feedback/feedbacks/{feedback_id}")
async def get_feedback(feedback_id: str):
    try:
        response = requests.get(f"{STUDENT_FEEDBACK_URL}/feedbacks/{feedback_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Student feedback service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.put("/student-feedback/feedbacks/{feedback_id}")
async def update_feedback(feedback_id: str, feedback: dict):
    try:
        response = requests.put(f"{STUDENT_FEEDBACK_URL}/feedbacks/{feedback_id}", json=feedback)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Student feedback service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

@app.delete("/student-feedback/feedbacks/{feedback_id}")
async def delete_feedback(feedback_id: str):
    try:
        response = requests.delete(f"{STUDENT_FEEDBACK_URL}/feedbacks/{feedback_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Student feedback service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)

# Integrated endpoints
@app.get("/integrated/user/{user_id}/dashboard")
async def get_user_dashboard(user_id: str):
    if not INTEGRATION_LAYER_URL:
        raise HTTPException(status_code=503, detail="Integration layer not configured")

    try:
        response = requests.get(f"{INTEGRATION_LAYER_URL}/integrated/user/{user_id}/dashboard")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting integrated dashboard: {str(e)}")
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)
        else:
            status_code = 503
            error_detail = f"Integration service unavailable: {str(e)}"

        raise HTTPException(status_code=status_code, detail=error_detail)
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import logging
from jose import jwt, JWTError
from passlib.context import CryptContext
import asyncio
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("integration-layer")

# Initialize FastAPI app
app = FastAPI(
    title="Microservices Integration Layer",
    description="Integration layer for connecting multiple microservices platforms",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "integration_request_total", 
    "Total number of requests processed by the integration layer",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "integration_request_latency_seconds", 
    "Request latency in seconds",
    ["method", "endpoint"]
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Service URLs
OUR_API_GATEWAY_URL = os.getenv("OUR_API_GATEWAY_URL", "http://api-gateway:8000")
EXTERNAL_API_GATEWAY_URL = os.getenv("EXTERNAL_API_GATEWAY_URL", "http://external-api-gateway:9000")

# Service registry
SERVICE_REGISTRY = {
    # Our services
    "assignment": f"{OUR_API_GATEWAY_URL}/assignments",
    "grading": f"{OUR_API_GATEWAY_URL}/grades",
    "quiz": f"{OUR_API_GATEWAY_URL}/quizzes",
    "forum": f"{OUR_API_GATEWAY_URL}/forum",
    "content": f"{OUR_API_GATEWAY_URL}/content",
    
    # External team services (to be configured)
    "external_user": f"{EXTERNAL_API_GATEWAY_URL}/users",
    "external_notification": f"{EXTERNAL_API_GATEWAY_URL}/notifications",
    "external_payment": f"{EXTERNAL_API_GATEWAY_URL}/payments",
    "external_analytics": f"{EXTERNAL_API_GATEWAY_URL}/analytics",
}

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    service: Optional[str] = None
    scopes: List[str] = []

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

# Middleware for request timing and metrics
@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status = response.status_code
    
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(process_time)
    
    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        service = payload.get("service")
        scopes = payload.get("scopes", [])
        if username is None and service is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_data = TokenData(username=username, service=service, scopes=scopes)
        return token_data
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Check our API gateway
        async with httpx.AsyncClient() as client:
            our_response = await client.get(f"{OUR_API_GATEWAY_URL}/health", timeout=5.0)
            
        # Try to check external API gateway if configured
        external_status = "not_configured"
        if EXTERNAL_API_GATEWAY_URL != "http://external-api-gateway:9000":
            try:
                async with httpx.AsyncClient() as client:
                    external_response = await client.get(f"{EXTERNAL_API_GATEWAY_URL}/health", timeout=5.0)
                external_status = "healthy" if external_response.status_code == 200 else "unhealthy"
            except:
                external_status = "unreachable"
        
        return {
            "status": "healthy",
            "our_platform": "healthy" if our_response.status_code == 200 else "unhealthy",
            "external_platform": external_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Service discovery endpoint
@app.get("/services")
async def list_services():
    return {
        "our_services": [
            {"name": "assignment", "url": SERVICE_REGISTRY["assignment"]},
            {"name": "grading", "url": SERVICE_REGISTRY["grading"]},
            {"name": "quiz", "url": SERVICE_REGISTRY["quiz"]},
            {"name": "forum", "url": SERVICE_REGISTRY["forum"]},
            {"name": "content", "url": SERVICE_REGISTRY["content"]},
        ],
        "external_services": [
            {"name": "user", "url": SERVICE_REGISTRY["external_user"]},
            {"name": "notification", "url": SERVICE_REGISTRY["external_notification"]},
            {"name": "payment", "url": SERVICE_REGISTRY["external_payment"]},
            {"name": "analytics", "url": SERVICE_REGISTRY["external_analytics"]},
        ]
    }

# Generate service token
@app.post("/token/service")
async def create_service_token(service_name: str):
    # In production, this should be secured and only accessible by authorized services
    token_data = {
        "service": service_name,
        "scopes": ["service"],
    }
    access_token = create_access_token(
        data=token_data, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Generic service proxy
@app.post("/proxy", response_model=ServiceResponse)
async def proxy_request(request: ServiceRequest):
    if request.service not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Service '{request.service}' not found")
    
    base_url = SERVICE_REGISTRY[request.service]
    full_url = f"{base_url}/{request.endpoint.lstrip('/')}"
    
    headers = request.headers or {}
    
    try:
        async with httpx.AsyncClient() as client:
            if request.method.upper() == "GET":
                response = await client.get(
                    full_url, 
                    params=request.params, 
                    headers=headers,
                    timeout=30.0
                )
            elif request.method.upper() == "POST":
                response = await client.post(
                    full_url, 
                    json=request.data, 
                    headers=headers,
                    timeout=30.0
                )
            elif request.method.upper() == "PUT":
                response = await client.put(
                    full_url, 
                    json=request.data, 
                    headers=headers,
                    timeout=30.0
                )
            elif request.method.upper() == "DELETE":
                response = await client.delete(
                    full_url, 
                    headers=headers,
                    timeout=30.0
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")
            
            # Try to parse JSON response, fall back to text if not JSON
            try:
                content = response.json()
            except:
                content = response.text
                
            return ServiceResponse(
                status_code=response.status_code,
                content=content,
                headers=dict(response.headers)
            )
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to {full_url}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# Direct routes to external services
# These are examples and should be customized based on the actual external services

# External User Service
@app.get("/external/users")
async def get_external_users():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_REGISTRY['external_user']}")
            return response.json()
    except Exception as e:
        logger.error(f"Error accessing external user service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"External service unavailable: {str(e)}")

@app.get("/external/users/{user_id}")
async def get_external_user(user_id: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_REGISTRY['external_user']}/{user_id}")
            return response.json()
    except Exception as e:
        logger.error(f"Error accessing external user service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"External service unavailable: {str(e)}")

# External Notification Service
@app.post("/external/notifications")
async def send_notification(notification: Dict[str, Any]):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICE_REGISTRY['external_notification']}", 
                json=notification
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error accessing external notification service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"External service unavailable: {str(e)}")

# External Payment Service
@app.post("/external/payments")
async def process_payment(payment: Dict[str, Any]):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICE_REGISTRY['external_payment']}", 
                json=payment
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error accessing external payment service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"External service unavailable: {str(e)}")

# External Analytics Service
@app.get("/external/analytics")
async def get_analytics(start_date: str = None, end_date: str = None):
    try:
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICE_REGISTRY['external_analytics']}", 
                params=params
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error accessing external analytics service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"External service unavailable: {str(e)}")

# Integrated endpoints that combine data from multiple services
@app.get("/integrated/user/{user_id}/dashboard")
async def get_user_dashboard(user_id: str):
    """
    Get a comprehensive dashboard for a user by combining data from multiple services.
    This demonstrates how to integrate data from both your services and external services.
    """
    try:
        # Collect data from multiple services in parallel
        async with httpx.AsyncClient() as client:
            # Get user data from external service
            user_task = asyncio.create_task(
                client.get(f"{SERVICE_REGISTRY['external_user']}/{user_id}")
            )
            
            # Get assignments from our service
            assignments_task = asyncio.create_task(
                client.get(f"{SERVICE_REGISTRY['assignment']}?user_id={user_id}")
            )
            
            # Get quizzes from our service
            quizzes_task = asyncio.create_task(
                client.get(f"{SERVICE_REGISTRY['quiz']}?user_id={user_id}")
            )
            
            # Get grades from our service
            grades_task = asyncio.create_task(
                client.get(f"{SERVICE_REGISTRY['grading']}/student/{user_id}")
            )
            
            # Get analytics from external service
            analytics_task = asyncio.create_task(
                client.get(f"{SERVICE_REGISTRY['external_analytics']}?user_id={user_id}")
            )
            
            # Wait for all tasks to complete
            user_response, assignments_response, quizzes_response, grades_response, analytics_response = await asyncio.gather(
                user_task, assignments_task, quizzes_task, grades_task, analytics_task,
                return_exceptions=True
            )
        
        # Process responses, handling any exceptions
        user_data = user_response.json() if not isinstance(user_response, Exception) else {"error": str(user_response)}
        assignments = assignments_response.json() if not isinstance(assignments_response, Exception) else []
        quizzes = quizzes_response.json() if not isinstance(quizzes_response, Exception) else []
        grades = grades_response.json() if not isinstance(grades_response, Exception) else []
        analytics = analytics_response.json() if not isinstance(analytics_response, Exception) else {}
        
        # Combine the data
        dashboard = {
            "user": user_data,
            "academic": {
                "assignments": assignments,
                "quizzes": quizzes,
                "grades": grades
            },
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return dashboard
    except Exception as e:
        logger.error(f"Error generating user dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

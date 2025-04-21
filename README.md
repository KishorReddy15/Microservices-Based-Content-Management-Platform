# Content Management Platform

A comprehensive microservices-based educational content management platform that handles assignments, quizzes, content, forum discussions, grading, and student performance feedback. Built with FastAPI, Docker, and modern database technologies, this platform provides a scalable and modular solution for educational institutions and e-learning platforms.

## Features

- **Content Management**: Create, read, update, and delete educational content with rich text support
- **Assignment System**: Manage assignments, deadlines, and student submissions with file upload capabilities
- **Quiz System**: Create, update, delete, and grade quizzes with multiple question types and automatic scoring
- **Forum System**: Enable student discussions with topics, posts, and comments for collaborative learning
- **Grading System**: Handle assignment and quiz grading with customizable rubrics and feedback
- **Student Feedback System**: Provide detailed performance feedback to students beyond simple grades
- **Calendar Integration**: Schedule quizzes and view them on a calendar interface
- **API Gateway**: Centralized access to all services with unified authentication and request routing
- **Integration Layer**: Connect with external microservices platforms through a dedicated integration layer
- **Cross-Platform Communication**: Seamlessly integrate with other teams' microservices

## Technology Stack

### Backend Services

- **Framework**: FastAPI (Python)
- **Version**: 0.109.2 for most services, 0.68.1 for Forum Service
- **ASGI Server**: Uvicorn
- **API Documentation**: OpenAPI/Swagger UI (available at /docs endpoint for each service)
- **Authentication**: JWT-based token authentication
- **Validation**: Pydantic models for request/response validation

### Databases

1. **PostgreSQL** (Port 5432)

   - Version: 14
   - Used by: Assignment Service, Forum Service, Grading Service
   - Features: ACID compliance, relational data storage, complex queries
   - Connection: SQLAlchemy ORM with connection pooling
   - Schema: Automatically created on service startup

2. **MongoDB** (Port 27017)
   - Version: 4.4
   - Used by: Content Service, Quiz Service, Grading Service, Student Feedback Service, Calendar Service
   - Features: Document-based storage, flexible schema, high performance
   - Connection: PyMongo driver with connection pooling
   - Indexes: Automatically created for optimal query performance

### Containerization & Orchestration

- **Docker**: Container runtime for service isolation
- **Docker Compose**: Service orchestration and networking
- **Multi-stage builds**: Optimized container images for production
- **Health checks**: Automatic container health monitoring
- **Volume mounts**: Persistent storage for databases

### Development Tools

- **Python**: 3.9+
- **SQLAlchemy**: 1.4.23 (ORM for PostgreSQL)
- **PyMongo**: 3.12.0 (MongoDB driver)
- **Pydantic**: Version compatibility varies by service (1.8.2 - 2.6.1)
- **psycopg2**: 2.9.5 (PostgreSQL adapter)
- **Markdown**: 3.3.7 (For forum content formatting)
- **python-jose**: 3.3.0 (JWT token handling)
- **passlib**: 1.7.4 (Password hashing)

## Prerequisites

Before you begin, ensure you have the following installed:

- Docker (20.10+)
- Docker Compose (2.0+)
- Git
- curl (for testing endpoints)
- 4GB+ RAM available for containers

## Getting Started

1. **Clone the Repository**

   ```bash
   git clone https://github.com/KishorReddy15/Microservices-Based-Content-Management-Platform.git
   cd content-management-platform
   ```

2. **Start the Services**

   For standard deployment without integration:

   ```bash
   # Start all services in detached mode
   docker compose up -d

   # Verify services are running
   docker compose ps
   ```

   For deployment with integration capabilities:

   ```bash
   # Start all services including the integration layer
   docker compose -f docker-compose.integration.yml up -d

   # Verify services are running
   docker compose -f docker-compose.integration.yml ps
   ```

3. **Wait for Services to Initialize**

   ```bash
   # The first startup may take a few minutes as databases initialize
   # You can monitor the logs to see when services are ready
   docker compose logs -f
   ```

4. **Verify Service Health**

   ```bash
   # Check Content Service
   curl http://localhost:8005/health

   # Check Quiz Service
   curl http://localhost:8003/health

   # Check Assignment Service
   curl http://localhost:8001/health

   # Check Forum Service
   curl http://localhost:8004/health

   # Check Grading Service
   curl http://localhost:8002/health

   # Check API Gateway
   curl http://localhost:8000/health
   ```

5. **Access API Documentation**

   - Open your browser and navigate to:
     - API Gateway: http://localhost:8000/docs
     - Quiz Service: http://localhost:8003/docs
     - Forum Service: http://localhost:8004/docs
     - Assignment Service: http://localhost:8001/docs
     - Content Service: http://localhost:8005/docs
     - Grading Service: http://localhost:8002/docs
     - Student Feedback Service: http://localhost:8006/ (Welcome page)
     - Calendar Service: http://localhost:5000/api/events (Events list)

6. **Important Notes About URL Patterns**
   - Some services use trailing slashes in their URLs, while others don't:
     - Quiz Service: Use `/quizzes` (no trailing slash)
     - Forum Service: Use `/topics/` (with trailing slash)
     - Content Service: Use `/content/` (with trailing slash)
     - Assignment Service: Use `/assignments/` (with trailing slash)
   - When accessing through the API Gateway, follow the same pattern as the underlying service

## Service Details and API Examples

### API Gateway (Port 8000)

The API Gateway serves as the entry point for all client requests, routing them to the appropriate microservice.

```bash
# Health check
curl http://localhost:8000/health

# All service endpoints are available through the gateway
# For example, to access quiz service:
curl http://localhost:8000/quizzes
```

### Quiz Service (Port 8003)

The Quiz Service manages the creation, retrieval, updating, and deletion of quizzes.

```bash
# Create new quiz
curl -X POST http://localhost:8003/quizzes -H "Content-Type: application/json" -d '{
  "title": "Python Quiz",
  "description": "Test your Python knowledge",
  "questions": [
    {
      "type": "multiple_choice",
      "text": "What is Python?",
      "points": 1.0,
      "options": ["A programming language", "A snake", "A game"],
      "correct_answer": 0
    }
  ],
  "duration_minutes": 30
}'

# List all quizzes
curl http://localhost:8003/quizzes

# Get specific quiz
curl http://localhost:8003/quizzes/{quiz_id}

# Update quiz
curl -X PUT http://localhost:8003/quizzes/{quiz_id} -H "Content-Type: application/json" -d '{
  "title": "Updated Python Quiz",
  "description": "Updated description",
  "questions": [
    {
      "type": "multiple_choice",
      "text": "What is Python?",
      "points": 1.0,
      "options": ["A programming language", "A snake", "A game"],
      "correct_answer": 0
    }
  ],
  "duration_minutes": 45
}'

# Delete quiz
curl -X DELETE http://localhost:8003/quizzes/{quiz_id}

# Publish quiz (makes it available to students)
curl -X POST http://localhost:8003/quizzes/{quiz_id}/publish

# Get quiz statistics
curl http://localhost:8003/quizzes/{quiz_id}/statistics
```

### Forum Service (Port 8004)

The Forum Service enables discussions through topics and posts.

```bash
# Create new topic
curl -X POST http://localhost:8004/topics/ -H "Content-Type: application/json" -d '{
  "title": "Help with Python Assignment",
  "description": "Discussion about the Python assignment"
}'

# List all topics
curl http://localhost:8004/topics/

# Get specific topic
curl http://localhost:8004/topics/{topic_id}

# Create new post in a topic
curl -X POST http://localhost:8004/topics/{topic_id}/posts/ -H "Content-Type: application/json" -d '{
  "content": "I need help with my Python assignment...",
  "author": "Student Name"
}'

# List all posts in a topic
curl http://localhost:8004/topics/{topic_id}/posts/

# Get specific post
curl http://localhost:8004/topics/{topic_id}/posts/{post_id}

# Delete post
curl -X DELETE http://localhost:8004/topics/{topic_id}/posts/{post_id}
```

### Assignment Service (Port 8001)

The Assignment Service manages assignments and submissions.

```bash
# Create new assignment
curl -X POST http://localhost:8001/assignments/ -H "Content-Type: application/json" -d '{
  "title": "Python Basics Assignment",
  "description": "Create a simple Python program...",
  "due_date": "2024-04-01T23:59:59Z"
}'

# List all assignments
curl http://localhost:8001/assignments/

# Get specific assignment
curl http://localhost:8001/assignments/{assignment_id}

# Submit assignment
curl -X POST http://localhost:8001/assignments/{assignment_id}/submit -F "student_id=123" -F "file=@/path/to/your/file.py"

# Get assignment submissions
curl http://localhost:8001/assignments/{assignment_id}/submissions
```

### Content Service (Port 8005)

The Content Service manages educational content.

```bash
# Create new content
curl -X POST http://localhost:8005/content/ -H "Content-Type: application/json" -d '{
  "title": "Introduction to Python",
  "content": "Python is a high-level programming language...",
  "type": "tutorial"
}'

# List all content
curl http://localhost:8005/content/

# Get specific content
curl http://localhost:8005/content/{content_id}

# Update content
curl -X PUT http://localhost:8005/content/{content_id} -H "Content-Type: application/json" -d '{
  "title": "Updated Title",
  "content": "Updated content...",
  "type": "tutorial"
}'

# Delete content
curl -X DELETE http://localhost:8005/content/{content_id}
```

### Grading Service (Port 8002)

The Grading Service handles grading of assignments and quizzes, as well as integration with the Student Feedback Service.

```bash
# Grade assignment
curl -X POST http://localhost:8002/grades -H "Content-Type: application/json" -d '{
  "assignment_id": "assignment_id",
  "student_id": 101,
  "score": 85.5,
  "feedback": "Good work, but could improve..."
}'

# Grade quiz
curl -X POST http://localhost:8002/grade/quiz -H "Content-Type: application/json" -d '{
  "submission_id": "submission_id",
  "student_id": "student_id",
  "answers": [0, 1, 2]
}'

# Get grades for student
curl http://localhost:8002/grades/student/{student_id}

# Get grade with performance feedback
curl http://localhost:8002/grades/{assignment_id}/student/{student_id}/with-feedback

# Create performance feedback for a grade
curl -X POST http://localhost:8002/grades/{assignment_id}/student/{student_id}/performance-feedback -H "Content-Type: application/json" -d '{
  "mentor_id": "201",
  "feedback_text": "Your algorithm implementation needs improvement.",
  "performance_areas": [
    {"area": "Algorithm Design", "rating": 3, "comments": "Good understanding but needs optimization"},
    {"area": "Code Quality", "rating": 4, "comments": "Well-structured code"}
  ],
  "improvement_suggestions": ["Study time complexity", "Practice more problems"],
  "strengths": ["Good problem understanding", "Clean code structure"]
}'

# Get all performance feedbacks for a student
curl http://localhost:8002/students/{student_id}/performance-feedbacks
```

## Monitoring and Logs

```bash
# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs assignment-service
docker compose logs content-service
docker compose logs quiz-service
docker compose logs forum-service

# Follow logs in real-time
docker compose logs -f quiz-service

# Check service status
docker compose ps

# Check resource usage
docker stats
```

## Development

### Local Development Setup

1. **Environment Setup**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies for Each Service**

   ```bash
   cd quiz-service
   pip install -r requirements.txt

   cd ../forum-service
   pip install -r requirements.txt

   # Repeat for other services
   ```

3. **Running Services Locally**

   ```bash
   # Start databases with Docker
   docker compose up -d postgres mongodb

   # Run a service locally
   cd quiz-service
   uvicorn main:app --reload --port 8003
   ```

4. **Running Tests**
   ```bash
   pytest
   ```

### Code Style and Conventions

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Document all public APIs with docstrings
- Use async/await for all I/O operations
- Validate all inputs with Pydantic models

## Recent Fixes and Improvements

The following issues have been fixed and improvements added in the latest version:

1. **Quiz Service**:

   - Fixed create quiz functionality to properly handle async/await operations
   - Fixed delete quiz functionality to properly handle MongoDB operations
   - Improved error handling for all quiz operations
   - Added calendar integration for scheduling quizzes

2. **Assignment Service**:

   - Added `is_published` field to the assignment model
   - Fixed database schema migration to handle the new field
   - Fixed type mismatches between `assignment_id` in different functions

3. **Forum Service**:

   - Fixed database connection issues
   - Improved error handling for database operations
   - Removed duplicate health check endpoint

4. **API Gateway**:

   - Added missing routes for the content service
   - Added the content service URL to the health check endpoint
   - Improved error handling for all service routes
   - Added routes for the student feedback service

5. **Grading Service**:

   - Fixed the `Assignment` model to use `String` as the primary key type
   - Updated the `is_published` default value to match the assignment service
   - Added integration with the Student Feedback Service
   - Added endpoints for retrieving and creating performance feedback

6. **New Services**:
   - Added Student Feedback Service for detailed performance feedback
   - Integrated Calendar Service for scheduling quizzes and events

## Troubleshooting

### Common Issues and Solutions

#### 1. Service Not Starting

**Symptoms:**

- Container exits immediately
- Health check fails

**Solutions:**

```bash
# Check logs for the specific service
docker compose logs [service-name]

# Rebuild the service
docker compose build [service-name]

# Restart the service
docker compose up -d --force-recreate [service-name]
```

#### 2. Database Connection Issues

**Symptoms:**

- Service logs show database connection errors
- "Connection refused" errors

**Solutions:**

```bash
# Check if database containers are running
docker compose ps | grep postgres
docker compose ps | grep mongodb

# Check database logs
docker compose logs postgres
docker compose logs mongodb

# Restart databases
docker compose restart postgres mongodb
```

#### 3. API Gateway Routing Issues

**Symptoms:**

- 404 errors when accessing services through gateway
- Gateway returns unexpected errors

**Solutions:**

```bash
# Check API gateway logs
docker compose logs api-gateway

# Verify service is running and healthy
curl http://localhost:[service-port]/health

# Restart API gateway
docker compose restart api-gateway
```

#### 4. Quiz Service Issues

**Symptoms:**

- Cannot create or delete quizzes
- Quiz operations return errors

**Solutions:**

```bash
# Check MongoDB connection
docker compose logs mongodb

# Verify quiz service is running
curl http://localhost:8003/health

# Restart quiz service
docker compose restart quiz-service
```

#### 5. Forum Service Issues

**Symptoms:**

- Cannot create topics or posts
- PostgreSQL connection errors

**Solutions:**

```bash
# Check PostgreSQL connection
docker compose logs postgres

# Verify forum service is running
curl http://localhost:8004/health

# Restart forum service
docker compose restart forum-service
```

### Advanced Troubleshooting

1. **Reset All Services**

   ```bash
   # Stop all services
   docker compose down

   # Remove all containers and volumes
   docker compose down -v

   # Rebuild and start
   docker compose up -d --build
   ```

2. **Check Resource Usage**

   ```bash
   # Check container resource usage
   docker stats

   # If memory usage is high, increase Docker memory allocation
   ```

3. **Database Inspection**

   ```bash
   # Connect to PostgreSQL
   docker compose exec postgres psql -U postgres -d content_management

   # Connect to MongoDB
   docker compose exec mongodb mongosh
   ```

## Integration with Other Microservices

This platform is designed to integrate seamlessly with other microservices platforms. For detailed integration instructions, see the [INTEGRATION.md](INTEGRATION.md) file and [STUDENT_FEEDBACK_INTEGRATION.md](STUDENT_FEEDBACK_INTEGRATION.md) for the student feedback service integration.

### Integration Features

1. **Integration Layer**: A dedicated service that handles cross-platform communication
2. **External Service Access**: Access external microservices through the API Gateway
3. **Shared Data Models**: Common models for consistent data exchange
4. **Service Discovery**: Automatic discovery of available services
5. **Distributed Tracing**: End-to-end request tracing across services
6. **Metrics Collection**: Centralized metrics for all integrated services
7. **API-Based Communication**: Services communicate via HTTP requests
8. **Background Tasks**: Asynchronous processing for non-blocking operations

### Integration Examples

#### Student Feedback Service Integration

```bash
# Get student feedback through the grading service
curl http://localhost:8002/students/101/performance-feedbacks

# Get student feedback through the API gateway
curl http://localhost:8000/student-feedback/students/101/feedbacks

# Create performance feedback for a grade
curl -X POST http://localhost:8002/grades/assignment-123/student/101/performance-feedback -H "Content-Type: application/json" -d '{
  "mentor_id": "201",
  "feedback_text": "Your algorithm implementation needs improvement.",
  "performance_areas": [
    {"area": "Algorithm Design", "rating": 3, "comments": "Good understanding but needs optimization"}
  ],
  "improvement_suggestions": ["Study time complexity"],
  "strengths": ["Good problem understanding"]
}'
```

#### Calendar Service Integration

```bash
# Create a quiz with scheduling
curl -X POST http://localhost:8003/quizzes -H "Content-Type: application/json" -d '{
  "title": "Integration Test Quiz",
  "description": "Testing the calendar integration",
  "questions": [
    {
      "type": "multiple_choice",
      "text": "What is 2+2?",
      "points": 1.0,
      "options": ["3", "4", "5"],
      "correct_answer": 1
    }
  ],
  "duration_minutes": 45,
  "is_scheduled": true,
  "scheduled_date": "2025-06-01T14:00:00",
  "auto_publish": true
}'

# View calendar events
curl http://localhost:5000/api/events
```

## Known Issues and Future Improvements

### Known Issues

1. **API Gateway Forum Service Routing**:

   - The API gateway does not correctly route requests to the forum service
   - Workaround: Access the forum service directly at http://localhost:8004

2. **Grading Service Retrieval**:

   - Cannot retrieve grades by student ID (returns "Not Found")
   - No endpoint to retrieve all grades

3. **URL Pattern Inconsistency**:

   - Some services use trailing slashes, others don't
   - This can cause confusion when making API requests

4. **Calendar Service Health Check**:

   - The calendar service does not have a health check endpoint
   - Workaround: Check if the service is running by accessing http://localhost:5000/api/events

5. **Student Feedback Service Health Check**:
   - The student feedback service does not have a health check endpoint
   - Workaround: Check if the service is running by accessing http://localhost:8006/

### Planned Improvements

1. **Authentication and Authorization**:

   - Implement JWT-based authentication across all services
   - Add role-based access control (RBAC)

2. **API Gateway Enhancements**:

   - Fix forum service routing
   - Add rate limiting
   - Implement request logging

3. **Service Enhancements**:

   - Add more comprehensive error handling
   - Improve cross-service communication
   - Add more test coverage
   - Add health check endpoints to all services

4. **Documentation**:

   - Add API documentation for each service
   - Add more examples and tutorials

5. **Integration Enhancements**:

   - Add more robust error handling for service integrations
   - Implement circuit breakers for service calls
   - Add metrics collection for integration performance

6. **Student Feedback Service**:
   - Add more detailed analytics for student performance
   - Implement AI-based feedback suggestions
   - Add visualization of student progress over time

## Contributing

We welcome contributions to improve the Content Management Platform!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows our style guidelines and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Content Management Platform - Microservice Integrations

This document provides details on the microservice integrations implemented in the content management platform.

## Overview of Microservices

The platform consists of the following microservices:

1. Assignment Service (Port 8001)
2. Grading Service (Port 8002)
3. Quiz Service (Port 8003)
4. Forum Service (Port 8004)
5. Content Service (Port 8005)
6. Student Feedback Service (Port 8006)
7. Calendar Service (Port 5000)
8. API Gateway (Port 8000)
9. PostgreSQL Database (Port 5432)
10. MongoDB Database (Port 27017)

## Integrations Implemented

### 1. Student Feedback Service Integration with Grading Service

#### Purpose
The integration between the Student Feedback Service and the Grading Service allows for comprehensive student assessment by combining grades with detailed performance feedback.

#### Implementation Details

1. **Feedback Client in Grading Service**:
   - Created a client module (`grading-service/feedback_integration/client.py`) that handles communication with the Student Feedback Service
   - The client uses HTTP requests to interact with the Student Feedback Service API
   - Added error handling to manage cases where the Student Feedback Service is unavailable

2. **New Endpoints in Grading Service**:
   - `GET /grades/{assignment_id}/student/{student_id}/with-feedback`: Retrieves a grade along with detailed feedback and performance feedback
   - `POST /grades/{assignment_id}/student/{student_id}/performance-feedback`: Creates performance feedback for a student's assignment
   - `GET /students/{student_id}/performance-feedbacks`: Retrieves all performance feedbacks for a student

3. **Background Tasks**:
   - Implemented background tasks for creating performance feedback to avoid blocking the response
   - Used FastAPI's BackgroundTasks feature to handle asynchronous processing

4. **API Gateway Integration**:
   - Added routes in the API Gateway to proxy requests to the Student Feedback Service
   - Configured the path prefix `/student-feedback` for all Student Feedback Service endpoints

5. **Docker Compose Configuration**:
   - Added the Student Feedback Service to the docker-compose.yml file
   - Configured environment variables for service discovery
   - Set up dependencies between services to ensure proper startup order

6. **MongoDB Integration**:
   - The Student Feedback Service uses MongoDB to store feedback data
   - Implemented collections for students, mentors, and feedbacks

#### API Endpoints

**Student Feedback Service**:
- `GET /`: Welcome message
- `POST /admin/student/create`: Create a student
- `POST /admin/mentor/create`: Create a mentor
- `GET /admin/students`: List all students
- `GET /admin/mentors`: List all mentors
- `POST /mentor/feedback/create`: Create feedback for a student
- `GET /mentor/{mentor_id}/feedbacks`: Get all feedbacks created by a mentor
- `GET /student/{student_id}/feedbacks`: Get all feedbacks for a student

**Grading Service (New Endpoints)**:
- `GET /grades/{assignment_id}/student/{student_id}/with-feedback`: Get a grade with feedback
- `POST /grades/{assignment_id}/student/{student_id}/performance-feedback`: Create performance feedback
- `GET /students/{student_id}/performance-feedbacks`: Get all performance feedbacks for a student

**API Gateway (New Routes)**:
- `GET /student-feedback/students/{student_id}/feedbacks`: Get all feedbacks for a student
- `POST /student-feedback/mentor/feedback/create`: Create feedback for a student
- Other Student Feedback Service endpoints are also accessible through the API Gateway

### 2. Quiz Service Integration with Calendar Service

#### Purpose
The integration between the Quiz Service and the Calendar Service allows for scheduling quizzes and displaying them on a calendar.

#### Implementation Details

1. **Calendar Integration in Quiz Service**:
   - When a quiz is scheduled, an event is created in the Calendar Service
   - The Quiz Service stores the calendar event ID for reference

2. **API-Based Communication**:
   - The Quiz Service communicates with the Calendar Service via HTTP requests
   - Events are created, updated, and deleted through the Calendar Service API

3. **Event Synchronization**:
   - When a quiz's schedule is updated, the corresponding calendar event is also updated
   - When a quiz is deleted, the corresponding calendar event is also deleted

## Testing the Integrations

### Testing Student Feedback Service Integration

1. **Create a Student and Mentor**:
   ```
   curl -X POST http://localhost:8006/admin/student/create -H "Content-Type: application/json" -d '{
     "student_id": "101",
     "name": "John Doe",
     "email": "john.doe@example.com",
     "department": "Computer Science"
   }'

   curl -X POST http://localhost:8006/admin/mentor/create -H "Content-Type: application/json" -d '{
     "mentor_id": "201",
     "name": "Jane Smith",
     "email": "jane.smith@example.com",
     "department": "Computer Science"
   }'
   ```

2. **Create Feedback**:
   ```
   curl -X POST http://localhost:8006/mentor/feedback/create -H "Content-Type: application/json" -d '{
     "student_id": "101",
     "mentor_id": "201",
     "feedback": "You need to improve your algorithm efficiency.",
     "highlights": ["Good problem understanding", "Clean code structure"]
   }'
   ```

3. **Create a Grade**:
   ```
   curl -X POST http://localhost:8002/grades -H "Content-Type: application/json" -d '{
     "assignment_id": "test-assignment-123",
     "student_id": 101,
     "score": 85.5,
     "feedback": "Good work, but could improve on the implementation details."
   }'
   ```

4. **Create Performance Feedback for the Grade**:
   ```
   curl -X POST http://localhost:8002/grades/test-assignment-123/student/101/performance-feedback -H "Content-Type: application/json" -d '{
     "mentor_id": "201",
     "feedback_text": "Your algorithm implementation needs improvement.",
     "performance_areas": [
       {"area": "Algorithm Design", "rating": 3, "comments": "Good understanding but needs optimization"},
       {"area": "Code Quality", "rating": 4, "comments": "Well-structured code"}
     ],
     "improvement_suggestions": ["Study time complexity", "Practice more problems"],
     "strengths": ["Good problem understanding", "Clean code structure"]
   }'
   ```

5. **Retrieve Grade with Feedback**:
   ```
   curl -s http://localhost:8002/grades/test-assignment-123/student/101/with-feedback
   ```

6. **Retrieve Feedback through API Gateway**:
   ```
   curl -s http://localhost:8000/student-feedback/students/101/feedbacks
   ```

### Testing Quiz Service and Calendar Service Integration

1. **Create a Quiz with Schedule**:
   ```
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
   ```

2. **Verify Calendar Event Creation**:
   ```
   curl -s http://localhost:5000/api/events
   ```

## Conclusion

The integrations implemented in the content management platform enhance its functionality by allowing data to flow between services. The Student Feedback Service integration with the Grading Service provides a more comprehensive student assessment system, while the Quiz Service integration with the Calendar Service improves scheduling and visibility of quizzes.

These integrations follow microservices best practices, using API-based communication, proper error handling, and asynchronous processing where appropriate. The platform is now more cohesive while maintaining the independence and scalability of individual services.

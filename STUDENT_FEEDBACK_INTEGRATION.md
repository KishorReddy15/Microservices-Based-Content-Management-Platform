# Student Feedback Service Integration

This document describes the integration between the Grading Service and the Student Feedback Service.

## Overview

The Student Feedback Service provides detailed performance feedback for students, which complements the grading functionality. This integration allows:

1. Retrieving student performance feedback alongside grades
2. Creating performance feedback for students through the Grading Service
3. Accessing the Student Feedback Service through the API Gateway

## Architecture

The integration follows a microservices architecture pattern with API-based communication:

- The Grading Service communicates with the Student Feedback Service via HTTP requests
- The API Gateway routes requests to the Student Feedback Service
- MongoDB is used to store feedback data

## Endpoints

### Grading Service

- `GET /grades/{assignment_id}/student/{student_id}/with-feedback`: Get a grade with student performance feedback
- `POST /grades/{assignment_id}/student/{student_id}/performance-feedback`: Create performance feedback for a student's assignment
- `GET /students/{student_id}/performance-feedbacks`: Get all performance feedbacks for a student

### Student Feedback Service

- `GET /student/{student_id}/feedbacks`: Get all feedbacks for a student
- `POST /mentor/feedback/create`: Create feedback for a student
- `GET /mentor/{mentor_id}/feedbacks`: Get all feedbacks created by a mentor

### API Gateway

- `GET /student-feedback/students/{student_id}/feedbacks`: Get all feedbacks for a student through the API Gateway

## Implementation Details

1. **Feedback Client**: A client class in the Grading Service that handles communication with the Student Feedback Service.

2. **Background Tasks**: Performance feedback creation is handled as a background task to avoid blocking the response.

3. **Error Handling**: Proper error handling is implemented to handle cases where the Student Feedback Service is unavailable.

## Testing

The integration has been tested with the following scenarios:

1. Creating a student and mentor in the Student Feedback Service
2. Creating feedback directly in the Student Feedback Service
3. Creating a grade in the Grading Service
4. Creating performance feedback for the grade through the Grading Service
5. Retrieving the grade with feedback from both services
6. Accessing the Student Feedback Service through the API Gateway

## Configuration

The integration requires the following environment variables:

- `STUDENT_FEEDBACK_SERVICE_URL`: The URL of the Student Feedback Service

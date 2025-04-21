import requests
import json
import os
from typing import Optional, Dict, Any, List, Union

# Student Feedback service URL
STUDENT_FEEDBACK_URL = os.getenv("STUDENT_FEEDBACK_URL", "http://student-feedback-service:8000")

class FeedbackClient:
    """Client for interacting with the Student Feedback service"""
    
    def __init__(self, base_url: str = STUDENT_FEEDBACK_URL):
        self.base_url = base_url
        
    def get_student_feedbacks(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get all feedbacks for a student
        
        Args:
            student_id: ID of the student
            
        Returns:
            List of feedback objects
        """
        try:
            response = requests.get(
                f"{self.base_url}/student/{student_id}/feedbacks"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting student feedbacks: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def get_feedback(self, feedback_id: str) -> Dict[str, Any]:
        """
        Get a specific feedback
        
        Args:
            feedback_id: ID of the feedback
            
        Returns:
            Feedback object
        """
        try:
            response = requests.get(
                f"{self.base_url}/feedbacks/{feedback_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting feedback: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def create_feedback(self, 
                       student_id: int, 
                       mentor_id: int, 
                       assignment_id: Optional[str] = None,
                       grade_id: Optional[str] = None,
                       feedback_text: str = "",
                       performance_areas: Optional[List[Dict[str, Any]]] = None,
                       improvement_suggestions: Optional[List[str]] = None,
                       strengths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new feedback
        
        Args:
            student_id: ID of the student
            mentor_id: ID of the mentor
            assignment_id: ID of the assignment (optional)
            grade_id: ID of the grade (optional)
            feedback_text: General feedback text
            performance_areas: List of performance areas with ratings
            improvement_suggestions: List of improvement suggestions
            strengths: List of strengths
            
        Returns:
            The created feedback object
        """
        feedback_data = {
            "student_id": student_id,
            "mentor_id": mentor_id,
            "feedback_text": feedback_text
        }
        
        if assignment_id:
            feedback_data["assignment_id"] = assignment_id
            
        if grade_id:
            feedback_data["grade_id"] = grade_id
            
        if performance_areas:
            feedback_data["performance_areas"] = performance_areas
            
        if improvement_suggestions:
            feedback_data["improvement_suggestions"] = improvement_suggestions
            
        if strengths:
            feedback_data["strengths"] = strengths
        
        try:
            response = requests.post(
                f"{self.base_url}/feedbacks",
                json=feedback_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating feedback: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def update_feedback(self, 
                       feedback_id: str,
                       feedback_text: Optional[str] = None,
                       performance_areas: Optional[List[Dict[str, Any]]] = None,
                       improvement_suggestions: Optional[List[str]] = None,
                       strengths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update an existing feedback
        
        Args:
            feedback_id: ID of the feedback to update
            feedback_text: New feedback text (if changing)
            performance_areas: New performance areas (if changing)
            improvement_suggestions: New improvement suggestions (if changing)
            strengths: New strengths (if changing)
            
        Returns:
            The updated feedback object
        """
        feedback_data = {}
        
        if feedback_text is not None:
            feedback_data["feedback_text"] = feedback_text
            
        if performance_areas is not None:
            feedback_data["performance_areas"] = performance_areas
            
        if improvement_suggestions is not None:
            feedback_data["improvement_suggestions"] = improvement_suggestions
            
        if strengths is not None:
            feedback_data["strengths"] = strengths
            
        try:
            response = requests.put(
                f"{self.base_url}/feedbacks/{feedback_id}",
                json=feedback_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error updating feedback: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def delete_feedback(self, feedback_id: str) -> Dict[str, Any]:
        """
        Delete a feedback
        
        Args:
            feedback_id: ID of the feedback to delete
            
        Returns:
            The response data
        """
        try:
            response = requests.delete(
                f"{self.base_url}/feedbacks/{feedback_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error deleting feedback: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

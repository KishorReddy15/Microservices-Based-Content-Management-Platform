from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Union
import asyncio
import threading
import time
import schedule
from .client import CalendarClient

class QuizScheduler:
    """
    Scheduler for quiz events that integrates with the calendar service
    and handles automatic publishing of scheduled quizzes.
    """

    def __init__(self, quiz_collection, calendar_client: Optional[CalendarClient] = None):
        self.quiz_collection = quiz_collection
        self.calendar_client = calendar_client or CalendarClient()
        self.scheduler_thread = None
        self.running = False

    def schedule_quiz(self, quiz_id: str, scheduled_date: datetime,
                     title: str, description: str, duration_minutes: int,
                     auto_publish: bool = False) -> Dict[str, Any]:
        """
        Schedule a quiz by creating a calendar event

        Args:
            quiz_id: ID of the quiz to schedule
            scheduled_date: When the quiz should be available
            title: Quiz title
            description: Quiz description
            duration_minutes: Duration of the quiz in minutes
            auto_publish: Whether to automatically publish the quiz at the scheduled time

        Returns:
            The created calendar event
        """
        # Calculate end time based on duration
        end_time = scheduled_date + timedelta(minutes=duration_minutes)

        # Create calendar event
        event = self.calendar_client.create_event(
            title=f"Quiz: {title}",
            start=scheduled_date,
            end=end_time,
            desc=f"Quiz: {description}\n\nDuration: {duration_minutes} minutes\nQuiz ID: {quiz_id}",
            created_by="quiz-service"
        )

        # Update quiz with scheduling information
        self.quiz_collection.update_one(
            {"_id": quiz_id},
            {
                "$set": {
                    "is_scheduled": True,
                    "scheduled_date": scheduled_date,
                    "calendar_event_id": event.get("_id"),
                    "auto_publish": auto_publish,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        return event

    def update_quiz_schedule(self, quiz_id: str, scheduled_date: datetime,
                           auto_publish: bool = None) -> Dict[str, Any]:
        """
        Update the schedule for a quiz

        Args:
            quiz_id: ID of the quiz to update
            scheduled_date: New scheduled date
            auto_publish: Whether to automatically publish (None = don't change)

        Returns:
            The updated calendar event
        """
        # Get the quiz
        quiz = self.quiz_collection.find_one({"_id": quiz_id})
        if not quiz:
            raise ValueError(f"Quiz with ID {quiz_id} not found")

        if not quiz.get("is_scheduled"):
            raise ValueError(f"Quiz with ID {quiz_id} is not scheduled")

        # Calculate end time based on duration
        end_time = scheduled_date + timedelta(minutes=quiz.get("duration_minutes", 60))

        # Update calendar event
        event = self.calendar_client.update_event(
            event_id=quiz.get("calendar_event_id"),
            start=scheduled_date,
            end=end_time
        )

        # Update quiz with new scheduling information
        update_data = {
            "scheduled_date": scheduled_date,
            "updated_at": datetime.now(timezone.utc)
        }

        if auto_publish is not None:
            update_data["auto_publish"] = auto_publish

        self.quiz_collection.update_one(
            {"_id": quiz_id},
            {"$set": update_data}
        )

        return event

    def cancel_quiz_schedule(self, quiz_id: str) -> Dict[str, Any]:
        """
        Cancel the schedule for a quiz

        Args:
            quiz_id: ID of the quiz to unschedule

        Returns:
            The response from deleting the calendar event
        """
        # Get the quiz
        quiz = self.quiz_collection.find_one({"_id": quiz_id})
        if not quiz:
            raise ValueError(f"Quiz with ID {quiz_id} not found")

        if not quiz.get("is_scheduled"):
            raise ValueError(f"Quiz with ID {quiz_id} is not scheduled")

        # Delete calendar event
        response = self.calendar_client.delete_event(quiz.get("calendar_event_id"))

        # Update quiz to remove scheduling information
        self.quiz_collection.update_one(
            {"_id": quiz_id},
            {
                "$set": {
                    "is_scheduled": False,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$unset": {
                    "scheduled_date": "",
                    "calendar_event_id": "",
                    "auto_publish": ""
                }
            }
        )

        return response

    def get_scheduled_quizzes(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled quizzes

        Returns:
            List of scheduled quizzes
        """
        quizzes = list(self.quiz_collection.find({"is_scheduled": True}))
        return [format_quiz_response(quiz) for quiz in quizzes]

    def get_upcoming_scheduled_quizzes(self) -> List[Dict[str, Any]]:
        """
        Get upcoming scheduled quizzes

        Returns:
            List of upcoming scheduled quizzes
        """
        now = datetime.now(timezone.utc)
        quizzes = list(self.quiz_collection.find({
            "is_scheduled": True,
            "scheduled_date": {"$gt": now}
        }).sort("scheduled_date", 1))

        return [format_quiz_response(quiz) for quiz in quizzes]

    def _check_and_publish_scheduled_quizzes(self):
        """Check for quizzes that need to be published and publish them"""
        now = datetime.now(timezone.utc)

        # Find quizzes that should be published
        quizzes_to_publish = list(self.quiz_collection.find({
            "is_scheduled": True,
            "auto_publish": True,
            "is_published": False,
            "scheduled_date": {"$lte": now}
        }))

        for quiz in quizzes_to_publish:
            try:
                print(f"Auto-publishing quiz: {quiz.get('title')} (ID: {quiz.get('_id')})")

                # Publish the quiz
                self.quiz_collection.update_one(
                    {"_id": quiz.get("_id")},
                    {
                        "$set": {
                            "is_published": True,
                            "updated_at": now
                        }
                    }
                )
            except Exception as e:
                print(f"Error auto-publishing quiz {quiz.get('_id')}: {str(e)}")

    def _scheduler_job(self):
        """Run scheduled jobs"""
        self._check_and_publish_scheduled_quizzes()

    def _run_scheduler(self):
        """Run the scheduler in a loop"""
        schedule.every(1).minutes.do(self._scheduler_job)

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return  # Already running

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        print("Quiz scheduler started")

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("Quiz scheduler stopped")

# Define a local version of format_quiz_response to avoid circular imports
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
    response["start_time"] = response.get("start_time", None)
    response["end_time"] = response.get("end_time", None)

    # Calendar integration fields
    response["is_scheduled"] = response.get("is_scheduled", False)
    response["scheduled_date"] = response.get("scheduled_date", None)
    response["calendar_event_id"] = response.get("calendar_event_id", None)
    response["auto_publish"] = response.get("auto_publish", False)

    return response

import requests
import json
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, Any, List, Union

# Calendar service URL
CALENDAR_SERVICE_URL = os.getenv("CALENDAR_SERVICE_URL", "http://calendar-service:5000")

class CalendarClient:
    """Client for interacting with the Calendar service"""
    
    def __init__(self, base_url: str = CALENDAR_SERVICE_URL):
        self.base_url = base_url
        
    def create_event(self, 
                    title: str, 
                    start: datetime, 
                    end: Optional[datetime] = None, 
                    desc: Optional[str] = None,
                    created_by: str = "quiz-service",
                    all_day: bool = False) -> Dict[str, Any]:
        """
        Create a new event in the calendar
        
        Args:
            title: Event title
            start: Start time
            end: End time (defaults to start + 1 hour if not provided)
            desc: Event description
            created_by: Creator identifier
            all_day: Whether this is an all-day event
            
        Returns:
            The created event data
        """
        if end is None:
            end = start + timedelta(hours=1)
            
        event_data = {
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "desc": desc or f"Quiz: {title}",
            "createdBy": created_by,
            "allDay": all_day
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/events",
                json=event_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating calendar event: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def update_event(self, 
                    event_id: str,
                    title: Optional[str] = None, 
                    start: Optional[datetime] = None, 
                    end: Optional[datetime] = None, 
                    desc: Optional[str] = None,
                    all_day: Optional[bool] = None) -> Dict[str, Any]:
        """
        Update an existing event in the calendar
        
        Args:
            event_id: ID of the event to update
            title: New event title (if changing)
            start: New start time (if changing)
            end: New end time (if changing)
            desc: New event description (if changing)
            all_day: New all-day flag (if changing)
            
        Returns:
            The updated event data
        """
        event_data = {}
        if title is not None:
            event_data["title"] = title
        if start is not None:
            event_data["start"] = start.isoformat()
        if end is not None:
            event_data["end"] = end.isoformat()
        if desc is not None:
            event_data["desc"] = desc
        if all_day is not None:
            event_data["allDay"] = all_day
            
        try:
            response = requests.put(
                f"{self.base_url}/api/events/{event_id}",
                json=event_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error updating calendar event: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """
        Delete an event from the calendar
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            The response data
        """
        try:
            response = requests.delete(
                f"{self.base_url}/api/events/{event_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error deleting calendar event: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def get_event(self, event_id: str) -> Dict[str, Any]:
        """
        Get an event from the calendar
        
        Args:
            event_id: ID of the event to retrieve
            
        Returns:
            The event data
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/events/{event_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting calendar event: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def get_upcoming_events(self) -> List[Dict[str, Any]]:
        """
        Get all upcoming events
        
        Returns:
            List of upcoming events
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/events/upcoming"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting upcoming events: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
            
    def get_events_in_range(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """
        Get events within a date range
        
        Args:
            start: Start date
            end: End date
            
        Returns:
            List of events in the range
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/events/range",
                params={
                    "start": start.isoformat(),
                    "end": end.isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting events in range: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

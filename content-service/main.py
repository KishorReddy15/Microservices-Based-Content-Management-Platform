from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Optional
from datetime import datetime
import os
from pydantic import BaseModel, Field
from bson import json_util
import json

app = FastAPI()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client.content_management
content_collection = db.content

class Content(BaseModel):
    title: str
    content: str
    type: str
    created_at: Optional[datetime] = None

class ContentResponse(BaseModel):
    id: str
    title: str
    content: str
    type: str
    created_at: datetime

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Create content
@app.post("/content/", response_model=ContentResponse)
async def create_content(content: Content):
    content_dict = content.dict()
    content_dict["created_at"] = datetime.utcnow()
    result = content_collection.insert_one(content_dict)
    content_dict["id"] = str(result.inserted_id)
    return ContentResponse(**content_dict)

# Get all content
@app.get("/content/", response_model=List[ContentResponse])
async def get_all_content():
    contents = []
    for content in content_collection.find():
        content["id"] = str(content.pop("_id"))
        contents.append(ContentResponse(**content))
    return contents

# Get content by ID
@app.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    content = content_collection.find_one({"_id": ObjectId(content_id)})
    if content:
        content["id"] = str(content.pop("_id"))
        return ContentResponse(**content)
    raise HTTPException(status_code=404, detail="Content not found")

# Update content
@app.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(content_id: str, content: Content):
    content_dict = content.dict()
    content_dict["created_at"] = datetime.utcnow()
    result = content_collection.update_one(
        {"_id": ObjectId(content_id)},
        {"$set": content_dict}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    content_dict["id"] = content_id
    return ContentResponse(**content_dict)

# Delete content
@app.delete("/content/{content_id}")
async def delete_content(content_id: str):
    result = content_collection.delete_one({"_id": ObjectId(content_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"status": "deleted", "id": content_id} 
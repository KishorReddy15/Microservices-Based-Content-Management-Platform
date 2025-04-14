from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/content_management")

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    # Database models
    class TopicDB(Base):
        __tablename__ = "topics"
        id = Column(String, primary_key=True)
        title = Column(String, nullable=False)
        description = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        posts = relationship("PostDB", back_populates="topic", cascade="all, delete-orphan")

    class PostDB(Base):
        __tablename__ = "posts"
        id = Column(String, primary_key=True)
        topic_id = Column(String, ForeignKey("topics.id"))
        content = Column(Text, nullable=False)
        author = Column(String, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        topic = relationship("TopicDB", back_populates="posts")

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Successfully connected to the database and created tables")
except Exception as e:
    print(f"Error connecting to the database: {e}")

# Pydantic models
class TopicBase(BaseModel):
    title: str
    description: str

class PostBase(BaseModel):
    content: str
    author: str

class PostResponse(PostBase):
    id: str
    topic_id: str
    created_at: datetime

    class Config:
        orm_mode = True

class TopicResponse(TopicBase):
    id: str
    created_at: datetime
    posts: List[PostResponse] = []

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create topic
@app.post("/topics/", response_model=TopicResponse)
async def create_topic(topic: TopicBase, db: Session = Depends(get_db)):
    db_topic = TopicDB(
        id=os.urandom(8).hex(),
        title=topic.title,
        description=topic.description
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

# Get all topics
@app.get("/topics/", response_model=List[TopicResponse])
async def get_all_topics(db: Session = Depends(get_db)):
    topics = db.query(TopicDB).all()
    return topics

# Get topic by ID
@app.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = db.query(TopicDB).filter(TopicDB.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

# Update topic
@app.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: str, topic: TopicBase, db: Session = Depends(get_db)):
    db_topic = db.query(TopicDB).filter(TopicDB.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db_topic.title = topic.title
    db_topic.description = topic.description

    db.commit()
    db.refresh(db_topic)
    return db_topic

# Delete topic
@app.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, db: Session = Depends(get_db)):
    db_topic = db.query(TopicDB).filter(TopicDB.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db.delete(db_topic)
    db.commit()
    return {"status": "deleted", "id": topic_id}

# Create post in topic
@app.post("/topics/{topic_id}/posts/", response_model=PostResponse)
async def create_post(topic_id: str, post: PostBase, db: Session = Depends(get_db)):
    topic = db.query(TopicDB).filter(TopicDB.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db_post = PostDB(
        id=os.urandom(8).hex(),
        topic_id=topic_id,
        content=post.content,
        author=post.author
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

# Get all posts in topic
@app.get("/topics/{topic_id}/posts/", response_model=List[PostResponse])
async def get_topic_posts(topic_id: str, db: Session = Depends(get_db)):
    topic = db.query(TopicDB).filter(TopicDB.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic.posts
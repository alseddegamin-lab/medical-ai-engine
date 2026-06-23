"""
Database models for medical questions
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json

Base = declarative_base()

# Association table for many-to-many relationship
question_subject_association = Table(
    'question_subject_association',
    Base.metadata,
    Column('question_id', Integer, ForeignKey('questions.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id'))
)

question_lesson_association = Table(
    'question_lesson_association',
    Base.metadata,
    Column('question_id', Integer, ForeignKey('questions.id')),
    Column('lesson_id', Integer, ForeignKey('lessons.id'))
)


class Subject(Base):
    """Medical subject (Anatomy, Physiology, etc.)"""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = relationship("Question", secondary=question_subject_association, back_populates="subjects")
    
    def __repr__(self):
        return f"<Subject {self.name}>"


class Lesson(Base):
    """Medical lesson/topic (Thyroid, Diabetes, etc.)"""
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject")
    questions = relationship("Question", secondary=question_lesson_association, back_populates="lessons")
    
    def __repr__(self):
        return f"<Lesson {self.name}>"


class Question(Base):
    """Medical question"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=True)
    option_e = Column(Text, nullable=True)
    correct_answer = Column(String(1), nullable=False)  # A, B, C, D, E
    explanation = Column(Text, nullable=False)
    
    # Metadata
    subject = Column(String(100), nullable=False)
    lesson = Column(String(100), nullable=False)
    high_yield = Column(Boolean, default=False)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    
    # Source information
    source_file = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    
    # Statistics
    times_attempted = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    average_time_seconds = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subjects = relationship("Subject", secondary=question_subject_association, back_populates="questions")
    lessons = relationship("Lesson", secondary=question_lesson_association, back_populates="questions")
    
    def __repr__(self):
        return f"<Question {self.id}: {self.question_text[:50]}...>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question": self.question_text,
            "options": [self.option_a, self.option_b, self.option_c, self.option_d, self.option_e],
            "correctAnswer": self.correct_answer,
            "explanation": self.explanation,
            "subject": self.subject,
            "lesson": self.lesson,
            "highYield": self.high_yield,
            "difficulty": self.difficulty,
            "sourceFile": self.source_file,
            "sourcePage": self.source_page,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class ImportJob(Base):
    """Track import jobs"""
    __tablename__ = "import_jobs"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, image
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    total_questions = Column(Integer, default=0)
    extracted_questions = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ImportJob {self.id}: {self.filename} ({self.status})>"


class UserProgress(Base):
    """Track user progress on questions"""
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False)  # Can be device ID or user ID
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    
    is_correct = Column(Boolean, nullable=False)
    time_spent_seconds = Column(Integer, nullable=True)
    attempts = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    question = relationship("Question")
    
    def __repr__(self):
        return f"<UserProgress user={self.user_id} question={self.question_id}>"

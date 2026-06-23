"""
Database connection and utilities
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from .models import Base, Question, Subject, Lesson, ImportJob, UserProgress
from src.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage database connections and operations"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database URL (default from settings)
        """
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database engine and session factory"""
        try:
            # Create engine
            if "sqlite" in self.database_url:
                # SQLite specific settings
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False
                )
                
                # Enable foreign keys for SQLite
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            else:
                # Other databases
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    echo=False
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database initialized: {self.database_url}")
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def add_question(self, session: Session, question_data: dict) -> Question:
        """Add a question to the database"""
        try:
            question = Question(
                question_text=question_data.get("question"),
                option_a=question_data.get("options", ["", "", "", ""])[0],
                option_b=question_data.get("options", ["", "", "", ""])[1],
                option_c=question_data.get("options", ["", "", "", ""])[2],
                option_d=question_data.get("options", ["", "", "", ""])[3] if len(question_data.get("options", [])) > 3 else None,
                option_e=question_data.get("options", ["", "", "", ""])[4] if len(question_data.get("options", [])) > 4 else None,
                correct_answer=question_data.get("correctAnswer"),
                explanation=question_data.get("explanation"),
                subject=question_data.get("subject"),
                lesson=question_data.get("lesson"),
                high_yield=question_data.get("highYield", False),
                difficulty=question_data.get("difficulty", "medium"),
                source_file=question_data.get("sourceFile"),
                source_page=question_data.get("sourcePage"),
            )
            session.add(question)
            session.flush()
            logger.info(f"Added question {question.id}")
            return question
        except Exception as e:
            logger.error(f"Error adding question: {e}")
            raise
    
    def add_questions_bulk(self, session: Session, questions_data: list) -> list:
        """Add multiple questions to the database"""
        added_questions = []
        for q_data in questions_data:
            try:
                question = self.add_question(session, q_data)
                added_questions.append(question)
            except Exception as e:
                logger.warning(f"Error adding question: {e}")
                continue
        
        logger.info(f"Added {len(added_questions)} questions")
        return added_questions
    
    def get_questions(self, session: Session, filters: dict = None) -> list:
        """Get questions with optional filters"""
        query = session.query(Question)
        
        if filters:
            if "subject" in filters:
                query = query.filter(Question.subject == filters["subject"])
            if "lesson" in filters:
                query = query.filter(Question.lesson == filters["lesson"])
            if "high_yield" in filters:
                query = query.filter(Question.high_yield == filters["high_yield"])
            if "difficulty" in filters:
                query = query.filter(Question.difficulty == filters["difficulty"])
        
        return query.all()
    
    def get_question_by_id(self, session: Session, question_id: int) -> Question:
        """Get a specific question"""
        return session.query(Question).filter(Question.id == question_id).first()
    
    def get_subjects(self, session: Session) -> list:
        """Get all subjects"""
        return session.query(Subject).all()
    
    def get_lessons(self, session: Session, subject_id: int = None) -> list:
        """Get lessons, optionally filtered by subject"""
        query = session.query(Lesson)
        if subject_id:
            query = query.filter(Lesson.subject_id == subject_id)
        return query.all()
    
    def get_import_job(self, session: Session, job_id: int) -> ImportJob:
        """Get import job status"""
        return session.query(ImportJob).filter(ImportJob.id == job_id).first()
    
    def create_import_job(self, session: Session, filename: str, file_type: str) -> ImportJob:
        """Create a new import job"""
        job = ImportJob(filename=filename, file_type=file_type)
        session.add(job)
        session.flush()
        logger.info(f"Created import job {job.id}")
        return job
    
    def update_import_job(self, session: Session, job_id: int, status: str, 
                         extracted_questions: int = None, error_message: str = None):
        """Update import job status"""
        job = session.query(ImportJob).filter(ImportJob.id == job_id).first()
        if job:
            job.status = status
            if extracted_questions is not None:
                job.extracted_questions = extracted_questions
            if error_message:
                job.error_message = error_message
            if status == "processing" and not job.started_at:
                from datetime import datetime
                job.started_at = datetime.utcnow()
            if status in ["completed", "failed"]:
                from datetime import datetime
                job.completed_at = datetime.utcnow()
            session.flush()
            logger.info(f"Updated import job {job_id}: {status}")
    
    def get_user_progress(self, session: Session, user_id: str, question_id: int = None):
        """Get user progress"""
        query = session.query(UserProgress).filter(UserProgress.user_id == user_id)
        if question_id:
            query = query.filter(UserProgress.question_id == question_id)
        return query.all()
    
    def record_user_progress(self, session: Session, user_id: str, question_id: int, 
                            is_correct: bool, time_spent_seconds: int = None):
        """Record user's attempt on a question"""
        progress = session.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.question_id == question_id
        ).first()
        
        if progress:
            progress.attempts += 1
            progress.is_correct = is_correct
            if time_spent_seconds:
                progress.time_spent_seconds = time_spent_seconds
        else:
            progress = UserProgress(
                user_id=user_id,
                question_id=question_id,
                is_correct=is_correct,
                time_spent_seconds=time_spent_seconds
            )
            session.add(progress)
        
        session.flush()
        logger.info(f"Recorded progress for user {user_id} on question {question_id}")
        return progress
    
    def get_statistics(self, session: Session, user_id: str = None) -> dict:
        """Get statistics"""
        total_questions = session.query(Question).count()
        
        stats = {
            "total_questions": total_questions,
            "subjects": session.query(Subject).count(),
            "lessons": session.query(Lesson).count(),
        }
        
        if user_id:
            user_progress = session.query(UserProgress).filter(
                UserProgress.user_id == user_id
            ).all()
            
            if user_progress:
                correct = sum(1 for p in user_progress if p.is_correct)
                stats["user_attempts"] = len(user_progress)
                stats["user_correct"] = correct
                stats["user_accuracy"] = (correct / len(user_progress)) * 100 if user_progress else 0
        
        return stats


# Global database manager instance
db_manager = DatabaseManager()

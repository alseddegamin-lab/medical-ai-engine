"""
FastAPI Server for Medical AI Engine
Provides REST API for question extraction and management
"""
import logging
import os
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.config import settings
from src.ocr import OCRProcessor, PDFProcessor
from src.deepseek import DeepSeekExtractor
from src.database import db_manager

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize FastAPI app
app = FastAPI(
    title="Medical AI Engine",
    description="Extract medical questions from PDFs and images using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
ocr_processor = None
deepseek_extractor = None

def initialize_components():
    """Initialize OCR and DeepSeek components"""
    global ocr_processor, deepseek_extractor
    
    try:
        ocr_processor = OCRProcessor(
            engine=settings.ocr_engine,
            language=settings.ocr_language,
            use_gpu=settings.ocr_use_gpu
        )
        logger.info("OCR processor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize OCR: {e}")
    
    try:
        deepseek_extractor = DeepSeekExtractor(
            api_key=settings.deepseek_api_key,
            api_url=settings.deepseek_api_url,
            model=settings.deepseek_model,
            temperature=settings.deepseek_temperature,
            max_tokens=settings.deepseek_max_tokens
        )
        logger.info("DeepSeek extractor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize DeepSeek: {e}")


# Pydantic models
class QuestionResponse(BaseModel):
    """Question response model"""
    id: int
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str
    subject: str
    lesson: str
    highYield: bool
    difficulty: str
    sourceFile: Optional[str] = None
    sourcePage: Optional[int] = None
    createdAt: str


class ExtractedQuestionsResponse(BaseModel):
    """Response for extracted questions"""
    job_id: int
    status: str
    total_extracted: int
    questions: List[dict]


class ImportJobResponse(BaseModel):
    """Import job response"""
    job_id: int
    filename: str
    file_type: str
    status: str
    extracted_questions: int
    error_message: Optional[str] = None


class StatisticsResponse(BaseModel):
    """Statistics response"""
    total_questions: int
    subjects: int
    lessons: int
    user_attempts: Optional[int] = None
    user_correct: Optional[int] = None
    user_accuracy: Optional[float] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("Starting Medical AI Engine...")
    initialize_components()
    logger.info("Medical AI Engine started successfully")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ocr_available": ocr_processor is not None,
        "deepseek_available": deepseek_extractor is not None,
    }


# Extract from PDF
@app.post("/extract/pdf")
async def extract_from_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Extract questions from PDF file
    
    Args:
        file: PDF file to process
        
    Returns:
        Extracted questions
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if not ocr_processor or not deepseek_extractor:
        raise HTTPException(status_code=503, detail="OCR or DeepSeek not initialized")
    
    try:
        # Save file temporarily
        file_path = settings.pdf_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing PDF: {file.filename}")
        
        # Extract text from PDF
        extracted_text = ocr_processor.extract_from_pdf(str(file_path))
        full_text = "\n".join(extracted_text.values())
        
        # Extract questions using DeepSeek
        questions = deepseek_extractor.extract_questions(full_text)
        
        # Save to database
        with db_manager.get_session() as session:
            for q in questions:
                q["sourceFile"] = file.filename
                db_manager.add_question(session, q)
        
        logger.info(f"Extracted {len(questions)} questions from {file.filename}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "total_extracted": len(questions),
            "questions": questions
        }
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up
        if file_path.exists():
            file_path.unlink()


# Extract from image
@app.post("/extract/image")
async def extract_from_image(file: UploadFile = File(...)):
    """
    Extract questions from image file
    
    Args:
        file: Image file to process
        
    Returns:
        Extracted questions
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if not ocr_processor or not deepseek_extractor:
        raise HTTPException(status_code=503, detail="OCR or DeepSeek not initialized")
    
    try:
        # Save file temporarily
        file_path = settings.image_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing image: {file.filename}")
        
        # Extract text from image
        text = ocr_processor.extract_from_image(str(file_path))
        
        # Extract questions using DeepSeek
        questions = deepseek_extractor.extract_questions(text)
        
        # Save to database
        with db_manager.get_session() as session:
            for q in questions:
                q["sourceFile"] = file.filename
                db_manager.add_question(session, q)
        
        logger.info(f"Extracted {len(questions)} questions from {file.filename}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "total_extracted": len(questions),
            "questions": questions
        }
    
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up
        if file_path.exists():
            file_path.unlink()


# Extract from text
@app.post("/extract/text")
async def extract_from_text(text: str):
    """
    Extract questions from text
    
    Args:
        text: Text containing questions
        
    Returns:
        Extracted questions
    """
    if not text or len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text is too short")
    
    if not deepseek_extractor:
        raise HTTPException(status_code=503, detail="DeepSeek not initialized")
    
    try:
        logger.info(f"Extracting from text (length: {len(text)})")
        
        # Extract questions using DeepSeek
        questions = deepseek_extractor.extract_questions(text)
        
        # Save to database
        with db_manager.get_session() as session:
            db_manager.add_questions_bulk(session, questions)
        
        logger.info(f"Extracted {len(questions)} questions from text")
        
        return {
            "status": "success",
            "total_extracted": len(questions),
            "questions": questions
        }
    
    except Exception as e:
        logger.error(f"Error extracting from text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get all questions
@app.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    subject: Optional[str] = Query(None),
    lesson: Optional[str] = Query(None),
    high_yield: Optional[bool] = Query(None),
    difficulty: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get questions with optional filters
    
    Args:
        subject: Filter by subject
        lesson: Filter by lesson
        high_yield: Filter by high yield
        difficulty: Filter by difficulty
        skip: Number of questions to skip
        limit: Number of questions to return
        
    Returns:
        List of questions
    """
    try:
        filters = {}
        if subject:
            filters["subject"] = subject
        if lesson:
            filters["lesson"] = lesson
        if high_yield is not None:
            filters["high_yield"] = high_yield
        if difficulty:
            filters["difficulty"] = difficulty
        
        with db_manager.get_session() as session:
            questions = db_manager.get_questions(session, filters)
            return [q.to_dict() for q in questions[skip:skip+limit]]
    
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get question by ID
@app.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int):
    """Get a specific question"""
    try:
        with db_manager.get_session() as session:
            question = db_manager.get_question_by_id(session, question_id)
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")
            return question.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get statistics
@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(user_id: Optional[str] = Query(None)):
    """Get statistics"""
    try:
        with db_manager.get_session() as session:
            stats = db_manager.get_statistics(session, user_id)
            return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Record user progress
@app.post("/progress")
async def record_progress(
    user_id: str,
    question_id: int,
    is_correct: bool,
    time_spent_seconds: Optional[int] = None
):
    """Record user's attempt on a question"""
    try:
        with db_manager.get_session() as session:
            db_manager.record_user_progress(
                session,
                user_id,
                question_id,
                is_correct,
                time_spent_seconds
            )
            return {"status": "success"}
    except Exception as e:
        logger.error(f"Error recording progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_server(host: str = None, port: int = None, reload: bool = None):
    """Run the FastAPI server"""
    host = host or settings.server_host
    port = port or settings.server_port
    reload = reload if reload is not None else settings.server_reload
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_server()

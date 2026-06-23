"""
CLI Tool for batch extraction of medical questions
Usage: python -m src.cli.extractor --input file.pdf --output questions.json
"""
import logging
import json
import argparse
from pathlib import Path
from typing import List
import sys

from src.config import settings
from src.ocr import OCRProcessor, PDFProcessor
from src.deepseek import DeepSeekExtractor
from src.database import db_manager

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class MedicalQuestionExtractor:
    """CLI tool for extracting medical questions"""
    
    def __init__(self):
        """Initialize extractor"""
        self.ocr_processor = OCRProcessor(
            engine=settings.ocr_engine,
            language=settings.ocr_language,
            use_gpu=settings.ocr_use_gpu
        )
        self.deepseek_extractor = DeepSeekExtractor(
            api_key=settings.deepseek_api_key,
            api_url=settings.deepseek_api_url,
            model=settings.deepseek_model,
            temperature=settings.deepseek_temperature,
            max_tokens=settings.deepseek_max_tokens
        )
        logger.info("Extractor initialized")
    
    def extract_from_pdf(self, pdf_path: str) -> List[dict]:
        """Extract questions from PDF"""
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Get PDF info
        pdf_info = PDFProcessor.get_pdf_info(pdf_path)
        logger.info(f"PDF info: {pdf_info}")
        
        # Extract text
        extracted_text = self.ocr_processor.extract_from_pdf(pdf_path)
        full_text = "\n".join(extracted_text.values())
        
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        
        # Extract questions
        questions = self.deepseek_extractor.extract_questions(full_text)
        
        logger.info(f"Extracted {len(questions)} questions")
        return questions
    
    def extract_from_image(self, image_path: str) -> List[dict]:
        """Extract questions from image"""
        logger.info(f"Processing image: {image_path}")
        
        # Extract text
        text = self.ocr_processor.extract_from_image(image_path)
        
        logger.info(f"Extracted {len(text)} characters from image")
        
        # Extract questions
        questions = self.deepseek_extractor.extract_questions(text)
        
        logger.info(f"Extracted {len(questions)} questions")
        return questions
    
    def extract_from_text_file(self, text_path: str) -> List[dict]:
        """Extract questions from text file"""
        logger.info(f"Processing text file: {text_path}")
        
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"Read {len(text)} characters from file")
        
        # Extract questions
        questions = self.deepseek_extractor.extract_questions(text)
        
        logger.info(f"Extracted {len(questions)} questions")
        return questions
    
    def save_to_json(self, questions: List[dict], output_path: str):
        """Save questions to JSON file"""
        logger.info(f"Saving to JSON: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(questions)} questions to {output_path}")
    
    def save_to_database(self, questions: List[dict], source_file: str = None):
        """Save questions to database"""
        logger.info(f"Saving to database...")
        
        with db_manager.get_session() as session:
            for q in questions:
                if source_file:
                    q["sourceFile"] = source_file
                db_manager.add_question(session, q)
        
        logger.info(f"Saved {len(questions)} questions to database")
    
    def process_file(self, input_path: str, output_path: str = None, 
                    save_to_db: bool = False, file_type: str = None):
        """Process a file and extract questions"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            logger.error(f"File not found: {input_path}")
            return False
        
        # Determine file type
        if file_type is None:
            suffix = input_path.suffix.lower()
            if suffix == ".pdf":
                file_type = "pdf"
            elif suffix in [".jpg", ".jpeg", ".png", ".gif"]:
                file_type = "image"
            elif suffix == ".txt":
                file_type = "text"
            else:
                logger.error(f"Unknown file type: {suffix}")
                return False
        
        # Extract questions
        try:
            if file_type == "pdf":
                questions = self.extract_from_pdf(str(input_path))
            elif file_type == "image":
                questions = self.extract_from_image(str(input_path))
            elif file_type == "text":
                questions = self.extract_from_text_file(str(input_path))
            else:
                logger.error(f"Unknown file type: {file_type}")
                return False
            
            if not questions:
                logger.warning("No questions extracted")
                return False
            
            # Save to JSON
            if output_path:
                self.save_to_json(questions, output_path)
            
            # Save to database
            if save_to_db:
                self.save_to_database(questions, source_file=input_path.name)
            
            logger.info(f"Successfully processed {input_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return False
    
    def process_directory(self, input_dir: str, output_dir: str = None, 
                         save_to_db: bool = False, pattern: str = "*.pdf"):
        """Process all files in a directory"""
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            logger.error(f"Directory not found: {input_dir}")
            return False
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        files = list(input_dir.glob(pattern))
        logger.info(f"Found {len(files)} files matching pattern: {pattern}")
        
        successful = 0
        for file_path in files:
            output_path = None
            if output_dir:
                output_path = output_dir / f"{file_path.stem}_questions.json"
            
            if self.process_file(str(file_path), str(output_path), save_to_db):
                successful += 1
        
        logger.info(f"Successfully processed {successful}/{len(files)} files")
        return successful == len(files)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Extract medical questions from PDFs, images, or text files"
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input file or directory path"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (optional)"
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["pdf", "image", "text"],
        help="File type (auto-detected if not specified)"
    )
    
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Save questions to database"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process directory instead of single file"
    )
    
    parser.add_argument(
        "--pattern", "-p",
        default="*.pdf",
        help="File pattern for batch processing (default: *.pdf)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize extractor
    try:
        extractor = MedicalQuestionExtractor()
    except Exception as e:
        logger.error(f"Failed to initialize extractor: {e}")
        return 1
    
    # Process files
    try:
        if args.batch:
            success = extractor.process_directory(
                args.input,
                args.output,
                args.save_db,
                args.pattern
            )
        else:
            success = extractor.process_file(
                args.input,
                args.output,
                args.save_db,
                args.type
            )
        
        return 0 if success else 1
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

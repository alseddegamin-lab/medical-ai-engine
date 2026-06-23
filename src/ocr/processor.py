"""
OCR Processor - Extract text from PDFs and images
Supports multiple OCR engines: PaddleOCR, EasyOCR
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Handle OCR for both PDFs and images"""
    
    def __init__(self, engine: str = "paddleocr", language: str = "en", use_gpu: bool = False):
        """
        Initialize OCR processor
        
        Args:
            engine: OCR engine to use (paddleocr, easyocr)
            language: Language for OCR (en, ar, en+ar)
            use_gpu: Whether to use GPU acceleration
        """
        self.engine = engine
        self.language = language
        self.use_gpu = use_gpu
        self.ocr_model = self._initialize_ocr()
        logger.info(f"OCR initialized with engine={engine}, language={language}, gpu={use_gpu}")
    
    def _initialize_ocr(self):
        """Initialize the OCR engine"""
        try:
            if self.engine == "paddleocr":
                from paddleocr import PaddleOCR
                return PaddleOCR(
                    use_angle_cls=True,
                    lang=self.language,
                    use_gpu=self.use_gpu,
                    show_log=False
                )
            elif self.engine == "easyocr":
                import easyocr
                lang_list = self.language.split("+") if "+" in self.language else [self.language]
                return easyocr.Reader(lang_list, gpu=self.use_gpu)
            else:
                raise ValueError(f"Unknown OCR engine: {self.engine}")
        except Exception as e:
            logger.error(f"Failed to initialize OCR: {e}")
            raise
    
    def extract_from_image(self, image_path: str) -> str:
        """
        Extract text from a single image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text
        """
        try:
            logger.info(f"Extracting text from image: {image_path}")
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            text = self._extract_text_from_image(image)
            logger.info(f"Extracted {len(text)} characters from image")
            return text
        except Exception as e:
            logger.error(f"Error extracting from image: {e}")
            raise
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract text from all pages of a PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with page numbers as keys and extracted text as values
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            from pdf2image import convert_from_path
            
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"PDF has {len(images)} pages")
            
            extracted_text = {}
            for page_num, image in enumerate(images, 1):
                try:
                    # Convert PIL image to numpy array
                    image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    text = self._extract_text_from_image(image_array)
                    extracted_text[f"page_{page_num}"] = text
                    logger.info(f"Extracted {len(text)} characters from page {page_num}")
                except Exception as e:
                    logger.warning(f"Error extracting from page {page_num}: {e}")
                    extracted_text[f"page_{page_num}"] = ""
            
            return extracted_text
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
            raise
    
    def _extract_text_from_image(self, image: np.ndarray) -> str:
        """
        Extract text from an image array using the OCR engine
        
        Args:
            image: Image as numpy array
            
        Returns:
            Extracted text
        """
        try:
            if self.engine == "paddleocr":
                result = self.ocr_model.ocr(image, cls=True)
                # PaddleOCR returns list of list of tuples
                text_lines = []
                if result:
                    for line in result:
                        if line:
                            for word_info in line:
                                text = word_info[1][0]  # Extract text
                                confidence = word_info[1][1]  # Extract confidence
                                if confidence > 0.3:  # Filter low confidence
                                    text_lines.append(text)
                return " ".join(text_lines)
            
            elif self.engine == "easyocr":
                result = self.ocr_model.readtext(image)
                # EasyOCR returns list of tuples
                text_lines = []
                for detection in result:
                    text = detection[1]  # Extract text
                    confidence = detection[2]  # Extract confidence
                    if confidence > 0.3:  # Filter low confidence
                        text_lines.append(text)
                return " ".join(text_lines)
            
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            raise
    
    def extract_from_bytes(self, file_bytes: bytes, file_type: str = "image") -> str:
        """
        Extract text from file bytes (for API uploads)
        
        Args:
            file_bytes: File content as bytes
            file_type: Type of file (image, pdf)
            
        Returns:
            Extracted text
        """
        try:
            if file_type == "image":
                # Convert bytes to image
                nparr = np.frombuffer(file_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return self._extract_text_from_image(image)
            
            elif file_type == "pdf":
                # Save bytes to temporary file and process
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                
                result = self.extract_from_pdf(tmp_path)
                # Combine all pages
                full_text = "\n".join(result.values())
                
                # Clean up
                Path(tmp_path).unlink()
                return full_text
            
        except Exception as e:
            logger.error(f"Error extracting from bytes: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(thresh, h=10)
            
            # Upscale if image is too small
            height, width = denoised.shape
            if width < 300 or height < 300:
                scale = max(300 / width, 300 / height)
                denoised = cv2.resize(denoised, None, fx=scale, fy=scale)
            
            return denoised
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image


class PDFProcessor:
    """Handle PDF-specific processing"""
    
    @staticmethod
    def get_pdf_info(pdf_path: str) -> Dict:
        """Get PDF metadata"""
        try:
            from PyPDF2 import PdfReader
            
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                return {
                    "total_pages": len(reader.pages),
                    "title": reader.metadata.title if reader.metadata else None,
                    "author": reader.metadata.author if reader.metadata else None,
                }
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            return {"total_pages": 0}
    
    @staticmethod
    def extract_text_from_pdf_text_layer(pdf_path: str) -> Dict[str, str]:
        """Extract text directly from PDF text layer (if available)"""
        try:
            from PyPDF2 import PdfReader
            
            extracted_text = {}
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    extracted_text[f"page_{page_num}"] = text
            
            return extracted_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF layer: {e}")
            return {}

"""
DeepSeek Integration - Extract medical questions using DeepSeek API
"""
import logging
import json
import time
from typing import Dict, List, Optional
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MedicalQuestion(BaseModel):
    """Medical question model"""
    question: str
    options: List[str] = Field(min_items=2, max_items=5)
    correctAnswer: str
    explanation: str
    subject: str  # Anatomy, Physiology, Biochemistry, etc.
    lesson: str  # Thyroid, Diabetes, etc.
    highYield: bool = False
    difficulty: str = "medium"  # easy, medium, hard


class DeepSeekExtractor:
    """Extract medical questions from text using DeepSeek"""
    
    MEDICAL_SUBJECTS = [
        "Anatomy",
        "Physiology",
        "Biochemistry",
        "Pathology",
        "Pharmacology",
        "Microbiology",
        "Parasitology",
        "Histology",
        "Immunology",
        "Genetics",
        "Community Medicine",
        "Surgery",
        "Internal Medicine",
        "Pediatrics",
        "Obstetrics",
        "Psychiatry",
    ]
    
    MEDICAL_LESSONS = {
        "Endocrine": ["Thyroid", "Diabetes", "Adrenal", "Pituitary", "Parathyroid"],
        "Cardiovascular": ["Hypertension", "Heart Failure", "Arrhythmia", "Coronary Artery Disease"],
        "Respiratory": ["Asthma", "COPD", "Pneumonia", "Tuberculosis"],
        "Gastrointestinal": ["Peptic Ulcer", "Inflammatory Bowel Disease", "Cirrhosis", "Hepatitis"],
        "Renal": ["Acute Kidney Injury", "Chronic Kidney Disease", "Nephrotic Syndrome"],
        "Hematology": ["Anemia", "Leukemia", "Thrombocytopenia"],
        "Neurology": ["Stroke", "Epilepsy", "Parkinson's", "Alzheimer's"],
        "Rheumatology": ["Rheumatoid Arthritis", "Systemic Lupus Erythematosus", "Osteoarthritis"],
    }
    
    def __init__(self, api_key: str, api_url: str = "https://api.deepseek.com/v1/chat/completions", 
                 model: str = "deepseek-chat", temperature: float = 0.3, max_tokens: int = 4000):
        """
        Initialize DeepSeek extractor
        
        Args:
            api_key: DeepSeek API key
            api_url: DeepSeek API endpoint
            model: Model name
            temperature: Temperature for generation
            max_tokens: Maximum tokens for response
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not api_key:
            raise ValueError("DeepSeek API key is required")
        
        logger.info(f"DeepSeekExtractor initialized with model={model}")
    
    def extract_questions(self, text: str, retry_count: int = 3) -> List[Dict]:
        """
        Extract medical questions from text
        
        Args:
            text: Input text containing questions
            retry_count: Number of retries on failure
            
        Returns:
            List of extracted questions as dictionaries
        """
        logger.info(f"Extracting questions from text (length: {len(text)})")
        
        prompt = self._build_extraction_prompt(text)
        
        for attempt in range(retry_count):
            try:
                response = self._call_deepseek(prompt)
                questions = self._parse_response(response)
                logger.info(f"Successfully extracted {len(questions)} questions")
                return questions
            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt + 1}: JSON parsing failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error extracting questions: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
        
        return []
    
    def _build_extraction_prompt(self, text: str) -> str:
        """Build the extraction prompt for DeepSeek"""
        subjects_list = ", ".join(self.MEDICAL_SUBJECTS)
        
        prompt = f"""You are an expert medical question extraction AI specialized in USMLE, MCCQE, and medical board exams.

Extract ALL Multiple Choice Questions (MCQs) from the provided medical text.

For EACH question, provide EXACTLY this JSON structure:
{{
  "question": "The exact question text",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correctAnswer": "The correct option text (must match exactly one option)",
  "explanation": "Detailed explanation of why this is correct and why others are wrong",
  "subject": "One of: {subjects_list}",
  "lesson": "Specific topic (e.g., Thyroid, Diabetes, Hypertension)",
  "highYield": true or false,
  "difficulty": "easy, medium, or hard"
}}

CRITICAL RULES:
1. Extract EVERY single question from the text
2. correctAnswer MUST exactly match one of the options
3. Return ONLY valid JSON array, no other text
4. If options have letters (A, B, C, D), remove them and keep only text
5. Ensure explanation is detailed and educational
6. Classify subject and lesson accurately
7. Mark as highYield if it's commonly tested

Return ONLY this format:
[
  {{...}},
  {{...}}
]

Medical text to extract from:
{text}"""
        
        return prompt
    
    def _call_deepseek(self, prompt: str) -> str:
        """Call DeepSeek API"""
        logger.info("Calling DeepSeek API...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a medical question extraction expert. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"DeepSeek API response received (length: {len(content)})")
            return content
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    def _parse_response(self, response: str) -> List[Dict]:
        """Parse DeepSeek response and validate questions"""
        logger.info("Parsing DeepSeek response...")
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            # Parse JSON
            questions = json.loads(response.strip())
            
            if not isinstance(questions, list):
                questions = [questions]
            
            # Validate and clean questions
            validated_questions = []
            for q in questions:
                try:
                    validated = self._validate_question(q)
                    validated_questions.append(validated)
                except ValueError as e:
                    logger.warning(f"Skipping invalid question: {e}")
                    continue
            
            logger.info(f"Parsed and validated {len(validated_questions)} questions")
            return validated_questions
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {response[:500]}")
            raise
    
    def _validate_question(self, question: Dict) -> Dict:
        """Validate and clean a question"""
        required_fields = ["question", "options", "correctAnswer", "explanation", "subject", "lesson"]
        
        # Check required fields
        for field in required_fields:
            if field not in question:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate options
        if not isinstance(question["options"], list) or len(question["options"]) < 2:
            raise ValueError("Options must be a list with at least 2 items")
        
        # Validate correctAnswer is in options
        if question["correctAnswer"] not in question["options"]:
            raise ValueError(f"correctAnswer '{question['correctAnswer']}' not in options")
        
        # Validate subject
        if question["subject"] not in self.MEDICAL_SUBJECTS:
            logger.warning(f"Unknown subject: {question['subject']}, using 'Internal Medicine'")
            question["subject"] = "Internal Medicine"
        
        # Clean up text fields
        question["question"] = question["question"].strip()
        question["explanation"] = question["explanation"].strip()
        question["options"] = [opt.strip() for opt in question["options"]]
        
        # Set defaults
        if "highYield" not in question:
            question["highYield"] = False
        if "difficulty" not in question:
            question["difficulty"] = "medium"
        
        return question
    
    def extract_from_multiple_texts(self, texts: List[str]) -> List[Dict]:
        """Extract questions from multiple text chunks"""
        all_questions = []
        
        for i, text in enumerate(texts, 1):
            logger.info(f"Processing text chunk {i}/{len(texts)}")
            try:
                questions = self.extract_questions(text)
                all_questions.extend(questions)
            except Exception as e:
                logger.error(f"Error processing text chunk {i}: {e}")
                continue
        
        logger.info(f"Total questions extracted: {len(all_questions)}")
        return all_questions

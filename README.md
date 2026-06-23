# Medical AI Engine 🏥

Professional medical question extraction engine using **Python + FastAPI + DeepSeek + OCR + SQLite**.

Extract medical questions from PDFs, images, and text with AI-powered classification and automatic database storage.

## Features ✨

- **📄 PDF Processing**: Extract text from multi-page PDFs with OCR
- **🖼 Image Recognition**: Extract text from medical images
- **🤖 AI-Powered Extraction**: Use DeepSeek to intelligently extract and classify questions
- **🏷 Automatic Classification**: 
  - Medical subjects (Anatomy, Physiology, Biochemistry, etc.)
  - Lessons/Topics (Thyroid, Diabetes, Hypertension, etc.)
  - Difficulty levels (Easy, Medium, Hard)
  - High-yield marking
- **💾 Database Storage**: SQLite with full question management
- **🔌 REST API**: FastAPI server for integration with apps
- **⚙️ CLI Tool**: Batch processing from command line
- **🔄 Fallback Support**: Multiple OCR engines and AI providers
- **📊 Statistics & Analytics**: Track user progress and performance

## Architecture

```
PDF/Image
    ↓
OCR (PaddleOCR/EasyOCR)
    ↓
Text Extraction
    ↓
DeepSeek API
    ↓
JSON Parsing & Validation
    ↓
SQLite Database
    ↓
REST API / React Native App
```

## Installation

### Prerequisites

- Python 3.8+
- pip or conda
- DeepSeek API key (get from https://console.deepseek.com/)

### Setup

1. **Clone/Download the project**
```bash
cd medical-ai-engine
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your DeepSeek API key
```

## Usage

### 1. FastAPI Server

Start the REST API server:

```bash
python -m src.api.server
```

Server runs on `http://localhost:8000`

**API Documentation**: http://localhost:8000/docs

### 2. CLI Tool

Extract questions from a single file:

```bash
# From PDF
python -m src.cli.extractor --input questions.pdf --output questions.json --save-db

# From image
python -m src.cli.extractor --input questions.jpg --output questions.json --save-db

# From text file
python -m src.cli.extractor --input questions.txt --output questions.json --save-db
```

Batch process a directory:

```bash
python -m src.cli.extractor --input ./pdfs --output ./output --save-db --batch --pattern "*.pdf"
```

### 3. Python API

Use directly in your code:

```python
from src.ocr import OCRProcessor
from src.deepseek import DeepSeekExtractor
from src.database import db_manager

# Initialize
ocr = OCRProcessor(engine="paddleocr", language="en")
extractor = DeepSeekExtractor(api_key="your-key")

# Extract from PDF
text = ocr.extract_from_pdf("questions.pdf")
questions = extractor.extract_questions(text)

# Save to database
with db_manager.get_session() as session:
    for q in questions:
        db_manager.add_question(session, q)
```

## REST API Endpoints

### Health Check
```
GET /health
```

### Extract from PDF
```
POST /extract/pdf
Content-Type: multipart/form-data

file: <PDF file>
```

### Extract from Image
```
POST /extract/image
Content-Type: multipart/form-data

file: <Image file>
```

### Extract from Text
```
POST /extract/text
Content-Type: application/json

{
  "text": "Your text with questions here..."
}
```

### Get Questions
```
GET /questions?subject=Physiology&lesson=Thyroid&high_yield=true&difficulty=medium&skip=0&limit=100
```

### Get Question by ID
```
GET /questions/{question_id}
```

### Get Statistics
```
GET /statistics?user_id=user123
```

### Record User Progress
```
POST /progress
Content-Type: application/json

{
  "user_id": "user123",
  "question_id": 42,
  "is_correct": true,
  "time_spent_seconds": 45
}
```

## Configuration

Edit `.env` file:

```env
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-key

# OCR Settings
OCR_ENGINE=paddleocr  # paddleocr or easyocr
OCR_LANGUAGE=en  # en, ar, en+ar
OCR_USE_GPU=false  # Use GPU for faster processing

# Database
DATABASE_URL=sqlite:///./medical_questions.db

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## Question Format

Extracted questions follow this structure:

```json
{
  "question": "What is the most common cause of hypothyroidism?",
  "options": [
    "Graves' disease",
    "Hashimoto's thyroiditis",
    "Thyroid cancer",
    "Iodine deficiency"
  ],
  "correctAnswer": "Hashimoto's thyroiditis",
  "explanation": "Hashimoto's thyroiditis is the most common cause of hypothyroidism in iodine-sufficient areas...",
  "subject": "Physiology",
  "lesson": "Thyroid",
  "highYield": true,
  "difficulty": "medium"
}
```

## Supported Medical Subjects

- Anatomy
- Physiology
- Biochemistry
- Pathology
- Pharmacology
- Microbiology
- Parasitology
- Histology
- Immunology
- Genetics
- Community Medicine
- Surgery
- Internal Medicine
- Pediatrics
- Obstetrics
- Psychiatry

## Database Schema

### Questions Table
- `id`: Question ID
- `question_text`: The question
- `option_a`, `option_b`, `option_c`, `option_d`, `option_e`: Answer options
- `correct_answer`: Correct option (A-E)
- `explanation`: Detailed explanation
- `subject`: Medical subject
- `lesson`: Specific lesson/topic
- `high_yield`: Is it commonly tested?
- `difficulty`: Easy/Medium/Hard
- `source_file`: Original file name
- `source_page`: Page number (for PDFs)

### User Progress Table
- `id`: Progress ID
- `user_id`: User identifier
- `question_id`: Question ID
- `is_correct`: Was answer correct?
- `time_spent_seconds`: Time taken
- `attempts`: Number of attempts

## Integration with OKSmed App

### 1. Install Medical AI Engine

```bash
pip install -r requirements.txt
```

### 2. Start the server

```bash
python -m src.api.server
```

### 3. In React Native app, configure API endpoint

```typescript
const API_URL = "http://your-server:8000";

// Upload PDF
const formData = new FormData();
formData.append("file", pdfFile);

const response = await fetch(`${API_URL}/extract/pdf`, {
  method: "POST",
  body: formData,
});

const questions = await response.json();
```

## Troubleshooting

### OCR not working
- Check if Tesseract/PaddleOCR is installed
- Try different OCR engine: `OCR_ENGINE=easyocr`
- Ensure image quality is good

### DeepSeek API errors
- Verify API key is correct
- Check API rate limits
- Ensure internet connection

### Slow processing
- Reduce PDF DPI: `PDF_DPI=150`
- Enable GPU: `OCR_USE_GPU=true`
- Process smaller files

### Database errors
- Delete `medical_questions.db` to reset
- Check file permissions
- Ensure SQLite is installed

## Performance Tips

1. **Use GPU**: Set `OCR_USE_GPU=true` for faster OCR
2. **Batch processing**: Process multiple files in parallel
3. **Optimize images**: Use high-quality, clear images
4. **Reduce PDF pages**: Split large PDFs into smaller chunks
5. **Cache results**: Store extracted questions to avoid re-processing

## Development

### Run tests
```bash
pytest tests/
```

### Format code
```bash
black src/
```

### Type checking
```bash
mypy src/
```

## License

MIT License - See LICENSE file

## Support

For issues, questions, or contributions, please contact the development team.

## Roadmap

- [ ] Support for more languages (Arabic, Spanish, French)
- [ ] Multi-language question extraction
- [ ] Advanced analytics dashboard
- [ ] Web UI for management
- [ ] Mobile app integration
- [ ] Question bank export/import
- [ ] Collaborative features
- [ ] Advanced filtering and search

---

**Built with ❤️ for medical education**

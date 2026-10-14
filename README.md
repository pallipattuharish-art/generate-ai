# 🎓 AI Study Assistant — Your Personal AI Learning Partner

> An intelligent, full-stack web application designed for students to transform lengthy lecture notes, PDFs, and Word documents into concise summaries, bilingual concept explanations in English & Telugu, interactive active-recall flashcards, and timed mock examinations with instant grading.

---

## 📌 1. Project Overview & Problem Statement

### The Problem
College and university students face an overwhelming volume of study material before exams. Manually summarizing 50+ page lecture decks, parsing complex technical definitions, and generating practice questions takes hours of tedious effort. Furthermore, students whose first language is not English frequently struggle to understand dense technical jargon without vernacular explanations.

### The Solution
**AI Study Assistant** provides an automated, student-centric revision companion:
- **Instant Extraction**: Safely parses text from PDF, DOCX, TXT, and Markdown files.
- **Structured Summarization**: Generates high-yield summaries with key definitions and formulas.
- **Bilingual Explanations**: Breaks down complex topics in **English** or **Telugu (తెలుగు)** across Beginner, Intermediate, and Advanced depths.
- **Practice Question Generator**: Produces 4-option MCQs with rationales, short-answer questions with model answers, and long essays with outlines.
- **Active Recall Flashcards**: Interactive 3D flip-card deck with shuffle, progress indicators, and self-evaluation tracking.
- **Timed Mock Exam Simulator**: Real countdown timer, one-question pacing, automated grading, and comprehensive answer rationales saved directly to SQLite.
- **Saved Materials Library**: Embedded SQLite storage for revision notes and test history with search, filtering, and deletion.

---

## 🚀 2. Technology Stack

- **Frontend**: HTML5, Modern CSS3 (CSS Variables, Flexbox/Grid, 3D CSS Card Flip, Dark/Light Themes), Vanilla JavaScript (Modular, zero heavy frameworks, accessible, responsive).
- **Backend**: Python 3.10+ / 3.13, Flask 3.1 (Application Factory, Blueprints, REST API).
- **Storage**: SQLite 3 (Zero configuration, embedded relational database with indexed queries).
- **Document Processing**: `pypdf` (PDF text extraction & scanned document detection), `python-docx` (Word documents), `werkzeug` (safe file sanitization).
- **AI Integration**: Configurable AI engine supporting **Google Gemini API** (`gemini-1.5-flash`), **OpenAI API** (`gpt-4o-mini`), and an **Offline Educational Demo Mode** (serves realistic sample responses when no API key is supplied).
- **Testing**: `pytest` automated test suite.

---

## 📁 3. Project Folder Structure

```text
AI PLANNER/
├── app.py                     # Flask application entry point & factory
├── config.py                  # Secure configuration loader from .env
├── database.py                # SQLite schema, migrations & CRUD operations
├── ai_service.py              # Isolated AI service adapter (Gemini, OpenAI, Demo Mode)
├── prompts.py                 # Structured prompts & anti-jailbreak input delimiters
├── file_processor.py          # Secure PDF, DOCX, TXT parser & OCR detector
├── requirements.txt           # Python dependency specifications
├── .env.example               # Template for environment variables
├── .env                       # Local environment configuration (git-ignored)
├── .gitignore                 # Excludes venv, sqlite databases, cache, and secrets
├── README.md                  # Comprehensive setup & architecture documentation
├── HACKATHON_PITCH.md         # Pitch script, judge Q&A, and demo plan
├── DEMO_CHECKLIST.md          # Step-by-step hackathon live demo guide
├── routes/
│   ├── __init__.py            # Blueprint registration package
│   ├── uploads.py             # File upload and text extraction endpoints
│   ├── study.py               # AI summaries, explanations, questions, flashcards
│   └── materials.py           # Saved library CRUD and quiz history
├── templates/
│   ├── base.html              # Master layout, navbar, light/dark switcher, toast alerts
│   ├── index.html             # Landing page with hero, features, and how it works
│   ├── dashboard.html         # Study metrics, tool launcher, and quiz history
│   ├── study.html             # Core interactive multi-tool study workspace
│   └── saved_materials.html   # Local SQLite study library and viewer modal
├── static/
│   ├── css/
│   │   └── style.css          # Design system with blue/purple accents & dark theme
│   ├── js/
│   │   ├── app.js             # Theme toggle, markdown parser, toast notifications
│   │   ├── study.js           # File upload handling, summarizer, concept explainer
│   │   ├── flashcards.js      # 3D flip cards, keyboard controls, shuffle, review
│   │   └── quiz.js            # Practice question grader & timed mock exam simulator
│   └── images/
│       └── logo.svg           # Application brand vector logo
└── tests/
    ├── __init__.py            # Test package
    ├── test_app.py            # Integration tests for routes, AI endpoints & database
    └── test_file_processor.py # Unit tests for PDF, DOCX, TXT extraction & validation
```

---

## 💻 4. Windows 11 Setup & Installation Guide

### Prerequisites
- Windows 11 (or Windows 10)
- Python 3.10 or higher installed ([Download Python](https://www.python.org/downloads/))
- Git (optional)

### Step 1: Open PowerShell
Open Windows PowerShell and navigate to the project directory:
```powershell
cd "c:\Users\phari\OneDrive\Documents\AI PLANNER"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(Note: If PowerShell displays an `ExecutionPolicy` error when activating, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` and try again).*

### Step 3: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 4: Configure Your AI API Key (Optional)
The application works immediately out-of-the-box in **Demo Mode** without an API key. To enable live Google Gemini AI generation:
1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` in Notepad:
   ```powershell
   notepad .env
   ```
3. Set your free Google Gemini API key:
   ```ini
   AI_PROVIDER=gemini
   GEMINI_API_KEY=AIzaSy...your_actual_key_here...
   GEMINI_MODEL=gemini-1.5-flash
   ```
   *(Get a free API key from [Google AI Studio](https://aistudio.google.com/)).*

### Step 5: Run Automated Tests
Execute the unit and integration test suite to verify everything is working:
```powershell
.\venv\Scripts\python.exe -m pytest -v
```
*(All 21 unit and integration tests will execute and pass).*

### Step 6: Start the Application
```powershell
.\venv\Scripts\python.exe app.py
```
Open your web browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🎯 5. Core Feature Tour

| Feature | Capabilities |
| :--- | :--- |
| **Document Ingestion** | Drag & drop PDF, DOCX, TXT, or MD files. Automatically extracts text, calculates word count, and detects non-selectable scanned PDFs (prompting for OCR). |
| **Notes Summarizer** | Generates Short, Medium, or Detailed revision summaries with key definitions, formulas, and bulleted pre-exam revision notes. |
| **Bilingual Explainer** | Explains concepts at Beginner, Intermediate, or Advanced levels in **English** or **Telugu (తెలుగు)** with analogies and self-check questions. |
| **Practice Generator** | Creates 5, 10, or 20 questions in MCQ (with immediate rationale), Short-Answer (with model answers), or Long-Answer (with essay outline & rubric). |
| **3D Flashcards** | Active recall deck with 3D flip card animations (click or spacebar), shuffle, progress indicator, and "Known" vs "Review" tracking. |
| **Timed Mock Exam** | Full examination simulator with real countdown timer, one-question navigation, auto-submit on time expiry, instant score percentage, and detailed answer rationale. |
| **Saved Library** | Embedded SQLite storage for materials and quiz scores with search by title/subject, filter by type, modal viewer, and one-click deletion. |

---

## 🛡️ 6. Security, Privacy & Prompt Hardening

1. **Anti-Prompt-Injection Architecture**: User notes are treated as untrusted data and strictly bounded inside `<<<STUDY_NOTES_START>>>` delimiters. System prompts explicitly instruct the model to ignore embedded commands or role overrides.
2. **Credential Isolation**: API keys are read strictly from `.env` on the server and are never exposed in HTML, client JavaScript, or network responses.
3. **Safe File Handling**: Filenames are sanitized via `werkzeug.utils.secure_filename`, files are limited to 16MB, and temporary upload files are cleaned up from disk immediately after text extraction.
4. **Data Privacy**: Stored notes and test results reside in a local SQLite file (`instance/study_assistant.db`). No cloud account or external tracking is used.

---

## ❓ 7. Common Errors & Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell ExecutionPolicy restriction | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` in PowerShell. |
| `pip is not recognized` | Python Scripts directory is not in system PATH | Use `python -m pip install -r requirements.txt` or `.\venv\Scripts\python.exe -m pip`. |
| `Scanned document detected` | Uploaded PDF contains images/scans rather than digital text | Use a digital PDF with selectable text, convert via OCR, or paste your text directly. |
| `Demo Mode banner visible` | No `GEMINI_API_KEY` configured in `.env` | Add a valid key in `.env` or continue testing using the offline educational sample generator. |

---

## 🔮 8. Future Enhancements

- Multi-tenant student authentication with cloud sync.
- Tesseract OCR integration for scanned textbook photos.
- Leitner-box spaced repetition algorithm for scheduled flashcard reviews.
- Text-to-speech audio explanations in Telugu and English.
- Export revision packs directly to Anki deck format (`.apkg`) and PDF cheat sheets.

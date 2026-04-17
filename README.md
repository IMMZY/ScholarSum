---
# ScholarSum 🎓
### Intelligent Academic Document Summarizer for Students

A web-based NLP tool that transforms long academic documents into clean, structured summaries – powered by OpenAI GPT-mini with a TF-IDF fallback engine.
---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Tech Stack](#tech-stack)
5. [Installation & Setup](#installation--setup)
6. [Running the App](#running-the-app)
7. [How It Works](#how-it-works)
8. [API Endpoints](#api-endpoints)
9. [Configuration](#configuration)
10. [Download Formats](#download-formats)
11. [Known Limitations](#known-limitations)
12. [Future Improvements](#future-improvements)

---

## Overview

Students in technical programs often face information overload when reading research papers, textbook chapters, and lengthy academic articles. **ScholarSum** addresses this by automatically extracting and summarizing the most important content from academic documents.

Users can upload a PDF or paste text directly, choose how long they want the summary to be, select an output language, and instantly receive:

- A structured **bullet point list** of key takeaways
- A flowing **paragraph summary**
- A list of **key terms** extracted from the document
- **Detected citations** from the source document
- A downloadable summary in **PDF, Word, or plain text** format

---

## Features

| Feature                | Description                                                              |
| ---------------------- | ------------------------------------------------------------------------ |
| PDF Upload             | Extract and summarize text from uploaded PDF files (no size limit)       |
| Text Input             | Paste raw text directly into the app                                     |
| GPT-4o-mini            | LLM-powered summarization for high-quality, structured output            |
| TF-IDF Fallback        | Rule-based summarization when no API key is configured                   |
| Summary Length Control | Slider (5%–50%) with Short / Medium / Detailed preset buttons            |
| Output Language        | Translate summary into 10 languages (requires OpenAI API)                |
| Bullet Points          | Key takeaways displayed as individual cards                              |
| Paragraph View         | Toggle to a flowing prose summary                                        |
| Copy to Clipboard      | One-click copy of the current view (bullets or paragraph)                |
| Keyword Extraction     | Top 10 domain-specific terms highlighted                                 |
| Citation Detection     | Automatically surfaces references and inline citations from the document |
| Dark / Light Mode      | Toggle between themes, preference saved across sessions                  |
| Download as PDF        | Clean, formatted PDF via ReportLab                                       |
| Download as Word       | Styled .docx file via python-docx                                        |
| Download as TXT        | Plain text summary report                                                |
| Smart File Naming      | Downloads named after source file (e.g. Paper_summarized.pdf)            |

---

## Project Structure

```
Sch_Sum/
│
├── app.py                  # Flask application — routes and API endpoints
├── Dockerfile              # Docker build configuration
├── .gitignore              # Excludes .env, uploads/, __pycache__, venv/
├── .dockerignore           # Excludes .env, .git, uploads/ from Docker image
│
├── core/                   # Python package — all backend logic
│   ├── __init__.py
│   ├── summarizer.py       # Entry point: delegates to OpenAI or TF-IDF
│   ├── openai_summarizer.py  # GPT-4o-mini summarization
│   ├── tfidf_summarizer.py   # TF-IDF extractive summarization + keyword extraction
│   ├── text_cleaner.py     # Junk filtering and text preprocessing
│   ├── citations.py        # Citation extraction (numbered refs + inline)
│   ├── pdf_extractor.py    # PDF text extraction using PyPDF2
│   └── exporter.py         # Export logic for PDF, DOCX, and TXT formats
│
├── static/
│   ├── style.css           # All CSS styles (dark/light theme via CSS variables)
│   └── main.js             # All frontend JavaScript
│
├── templates/
│   └── index.html          # HTML structure (links style.css and main.js)
│
├── uploads/                # Temporary folder for uploaded PDFs (auto-created)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## Tech Stack

### Backend

| Component          | Technology                    |
| ------------------ | ----------------------------- |
| Web Framework      | Flask (Python)                |
| Production Server  | Gunicorn                      |
| PDF Extraction     | PyPDF2                        |
| NLP / Tokenization | NLTK (punkt, stopwords)       |
| TF-IDF Scoring     | scikit-learn + custom scoring |
| LLM Summarization  | OpenAI API (gpt-4o-mini)      |
| PDF Export         | ReportLab                     |
| Word Export        | python-docx                   |
| Containerization   | Docker                        |

### Frontend

| Component     | Technology                                       |
| ------------- | ------------------------------------------------ |
| Markup        | HTML5                                            |
| Styling       | CSS3 with custom properties (dark/light theming) |
| Logic         | Vanilla JavaScript (static/main.js)              |
| HTTP Requests | Fetch API                                        |

---

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- pip
- An OpenAI API key (optional — TF-IDF works without one)

### Step 1 — Navigate to the project folder

```bash
cd path/to/Sch_Sum
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs:

```
flask
gunicorn
PyPDF2
nltk
scikit-learn
openai
fpdf2
reportlab
python-docx
python-dotenv
```

### Step 3 — NLTK Data

The app automatically downloads the required NLTK datasets (punkt, punkt_tab, stopwords) on first run. No manual action needed.

### Step 4 — Configure API key (optional)

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

If no `.env` is present, the app runs in TF-IDF fallback mode automatically.

---

## Running the App

### Option A — Python directly

```bash
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000
```

### Option B — Docker

```bash
# Build the image
docker build -t scholarsum .

# Run the container
docker run -p 8000:8000 --env-file .env scholarsum
```

Then open:

```
http://localhost:8000
```

> Always access the app via the server URL — do NOT open index.html directly in the browser, as the summarize button requires the Flask server to be running.

> Keep the terminal open while using the app. Closing it stops the server.

---

## How It Works

### Summarization Pipeline

```
User Input (PDF or Text)
        |
        v
  Text Extraction
  (PyPDF2 for PDF)
        |
        v
  OPENAI_API_KEY set?
   ┌────┴────┐
  YES       NO
   |         |
   v         v
GPT-4o-mini  TF-IDF Engine
(OpenAI API) (NLTK + custom scoring)
   |         |
   └────┬────┘
        |
        v
  Bullet Points + Paragraph + Keywords + Citations
        |
        v
  Display in Browser or Download
```

### GPT-4o-mini Mode

When an OpenAI API key is configured in `.env`, the document text is sent to gpt-4o-mini with a structured prompt instructing it to produce:

- 10 to 15 bullet points covering background, objectives, methods, results, and conclusions
- A 4 to 6 sentence paragraph summary in flowing academic prose

Output language can be set to any of the 10 supported languages. The model returns a structured BULLET_POINTS / PARAGRAPH format which is parsed server-side.

### TF-IDF Fallback Mode

When no API key is available, the app uses a custom extractive summarization pipeline:

1. **Preprocessing** — Text is cleaned at the line level to remove symbol noise, checkbox characters, and garbled PDF artifacts before sentence tokenization
2. **Junk Filtering** — Sentences are filtered to remove emails, URLs, table of contents lines, ALL-CAPS headers, and data rows
3. **Reference Stripping** — The References / Bibliography section is removed before scoring
4. **TF-IDF Scoring** — Each sentence is scored using Term Frequency × Inverse Document Frequency
5. **Positional Weighting** — Sentences from the introduction (first 10%) and conclusion (last 10%) receive a 1.4× score boost
6. **Extraction** — Top-ranked sentences (up to 10) are reordered by original position to maintain flow
7. **Keyword Extraction** — Top 10 terms identified by aggregating TF-IDF scores across all sentences

---

## API Endpoints

### GET /

Serves the main web interface.

---

### GET /api-status

Returns whether a valid OpenAI API key is configured.

**Response:** application/json

```json
{ "connected": true }
```

---

### POST /summarize

Summarizes a document.

**Request:** multipart/form-data

| Field          | Type    | Required         | Description                       |
| -------------- | ------- | ---------------- | --------------------------------- |
| text_input     | string  | One of these two | Raw text to summarize             |
| pdf_file       | file    | One of these two | PDF file to upload                |
| summary_length | integer | No               | Percentage (5–50), default: 20    |
| language       | string  | No               | Output language, default: English |

**Response:** application/json

```json
{
  "bullet_points": ["Point 1...", "Point 2..."],
  "paragraph": "A flowing summary paragraph...",
  "keywords": [
    ["word1", 0.42],
    ["word2", 0.38]
  ],
  "citations": ["Smith et al. (2021)", "Jones, A. (2019)..."],
  "original_word_count": 9839,
  "summary_word_count": 168,
  "sentence_count": 10,
  "method": "openai"
}
```

---

### POST /download

Generates and returns a downloadable summary file.

**Request:** application/json

```json
{
  "format": "pdf",
  "source_filename": "MyPaper.pdf",
  "bullet_points": ["..."],
  "paragraph": "...",
  "keywords": [["word", 0.42]],
  "original_word_count": 9839,
  "summary_word_count": 168
}
```

**Supported formats:** pdf, docx, txt

**Response:** File download stream with filename `{original_name}_summarized.{format}`

---

## Configuration

### OpenAI API Key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

The app reads this file directly on each request — no server restart needed after editing. If the file does not exist (e.g. on a deployment platform), the app reads from the system environment variable `OPENAI_API_KEY` instead.

To run in TF-IDF-only mode, simply omit the `.env` file or leave the key blank.

### Deploying to Railway (or similar platforms)

Set `OPENAI_API_KEY` as an environment variable in your platform's dashboard. The app detects it automatically — no `.env` file needed in production.

---

## Download Formats

| Format            | Library     | Contents                                                              |
| ----------------- | ----------- | --------------------------------------------------------------------- |
| PDF               | ReportLab   | Document Summary heading, paragraph summary, bullet points, key terms |
| Word (.docx)      | python-docx | Styled headings, paragraph summary, bullet list, key terms section    |
| Plain Text (.txt) | Built-in    | Simple formatted text report with all sections                        |

All downloads are named after the original uploaded file:

- MachineLearning.pdf becomes MachineLearning_summarized.pdf
- MachineLearning.pdf becomes MachineLearning_summarized.docx
- MachineLearning.pdf becomes MachineLearning_summarized.txt

---

## Known Limitations

- **Scanned PDFs** — PyPDF2 cannot extract text from image-based or scanned PDFs. OCR support is not currently implemented.
- **Very large PDFs** — Documents over approximately 12,000 words are truncated before being sent to the OpenAI API to stay within token limits. TF-IDF has no such limit.
- **TF-IDF coherence** — Extractive summaries may occasionally lack narrative flow since sentences are lifted directly from the source.
- **PDF formatting artifacts** — Some PDFs with complex layouts (multi-column, tables, footnotes) may produce garbled extracted text.
- **Translation** — Output language selection requires a valid OpenAI API key. TF-IDF fallback always outputs in the source document's language.

---

## Future Improvements

- OCR support for scanned PDFs (Tesseract integration)
- Support for .docx and .txt file uploads
- Multi-document comparison mode
- User accounts and summary history
- ROUGE score evaluation against human-written summaries

---

## Authors
Ime-Jnr Ime-Essien 
Onyekachi Odunze

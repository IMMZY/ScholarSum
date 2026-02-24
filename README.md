# ScholarSum 🎓
### Intelligent Academic Document Summarizer for Students

> A web-based NLP tool that transforms long academic documents into clean, structured summaries — powered by OpenAI GPT-4o-mini with a TF-IDF fallback engine.

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

Users can upload a PDF or paste text directly, choose how long they want the summary to be, and instantly receive:
- A structured **bullet point list** of key takeaways
- A flowing **paragraph summary**
- A list of **key terms** extracted from the document
- A downloadable summary in **PDF, Word, or plain text** format

---

## Features

| Feature | Description |
|---|---|
| PDF Upload | Extract and summarize text from uploaded PDF files |
| Text Input | Paste raw text directly into the app |
| GPT-4o-mini | LLM-powered summarization for high-quality, structured output |
| TF-IDF Fallback | Rule-based summarization when no API key is provided |
| Summary Length Control | Slider to choose summary length (5% to 50% of original) |
| Bullet Points | Key takeaways displayed as individual cards |
| Paragraph View | Toggle to a flowing prose summary |
| Keyword Extraction | Top 10 domain-specific terms highlighted |
| Download as PDF | Branded, formatted PDF via ReportLab |
| Download as Word | Styled .docx file via python-docx |
| Download as TXT | Plain text summary report |
| Smart File Naming | Downloads named after source file (e.g. Paper_summarized.pdf) |
| API Key Privacy | Key entered per-request, never stored server-side |

---

## Project Structure

```
Sch_Sum/
│
├── app.py                  # Flask application — routes and API endpoints
├── summarizer.py           # Summarization logic (OpenAI + TF-IDF)
├── pdf_extractor.py        # PDF text extraction using PyPDF2
├── exporter.py             # Export logic for PDF, DOCX, and TXT formats
│
├── static/
│   ├── style.css           # All CSS styles
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
| Component | Technology |
|---|---|
| Web Framework | Flask (Python) |
| PDF Extraction | PyPDF2 |
| NLP / Tokenization | NLTK (punkt, stopwords) |
| TF-IDF Scoring | Custom implementation using NLTK |
| LLM Summarization | OpenAI API (gpt-4o-mini) |
| PDF Export | ReportLab |
| Word Export | python-docx |

### Frontend
| Component | Technology |
|---|---|
| Markup | HTML5 |
| Styling | CSS3 (static/style.css) |
| Logic | Vanilla JavaScript (static/main.js) |
| HTTP Requests | Fetch API |

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
PyPDF2
nltk
scikit-learn
openai
reportlab
python-docx
```

### Step 3 — NLTK Data
The app automatically downloads the required NLTK datasets (punkt, punkt_tab, stopwords) on first run. No manual action needed.

---

## Running the App

```bash
python app.py
```

You should see:
```
* Serving Flask app 'app'
* Debug mode: off
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

Then open your browser and go to:
```
http://127.0.0.1:5000
```

> Always access the app via http://127.0.0.1:5000 — do NOT open index.html directly in the browser, as the summarize button requires the Flask server to be running.

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
  API Key provided?
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
  Bullet Points + Paragraph + Keywords
        |
        v
  Display in Browser or Download
```

### GPT-4o-mini Mode
When an OpenAI API key is provided, the document text is sent to gpt-4o-mini with a structured prompt instructing it to produce:
- 10 to 15 bullet points covering background, objectives, methods, results, and conclusions
- A 4 to 6 sentence paragraph summary in flowing academic prose

The model returns the response in a structured BULLET_POINTS / PARAGRAPH format which is parsed server-side.

### TF-IDF Fallback Mode
When no API key is provided, the app uses a custom extractive summarization pipeline:

1. **Preprocessing** — Text is cleaned and tokenized into sentences using NLTK's punkt tokenizer
2. **Junk Filtering** — Sentences are filtered to remove noise such as emails, URLs, table of contents lines, garbled PDF text, ALL-CAPS headers, and data rows
3. **TF-IDF Scoring** — Each sentence is scored using Term Frequency x Inverse Document Frequency to identify information-rich content
4. **Positional Weighting** — Sentences from the introduction (first 10%) and conclusion (last 10%) receive a score boost of 1.4x
5. **Extraction** — The top-ranked sentences (up to 10) are selected and reordered by their original position to maintain flow
6. **Keyword Extraction** — Top 10 terms are identified by aggregating TF-IDF scores across all sentences

---

## API Endpoints

### GET /
Serves the main web interface.

---

### POST /summarize
Summarizes a document.

**Request:** multipart/form-data

| Field | Type | Required | Description |
|---|---|---|---|
| text_input | string | One of these two | Raw text to summarize |
| pdf_file | file | One of these two | PDF file to upload |
| api_key | string | No | OpenAI API key |
| summary_length | integer | No | Percentage (5-50), default: 20 |

**Response:** application/json
```json
{
  "bullet_points": ["Point 1...", "Point 2..."],
  "paragraph": "A flowing summary paragraph...",
  "keywords": [["word1", 0.42], ["word2", 0.38]],
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

**Response:** File download stream with filename {original_name}_summarized.{format}

---

## Configuration

### OpenAI API Key
You can provide your API key in two ways:

**Option 1 — Via the UI (recommended)**
Enter your key in the OpenAI API Key field in the app. It is used only for that request and never stored.

**Option 2 — Via environment variable**
```bash
# Windows
set OPENAI_API_KEY=sk-...

# Mac / Linux
export OPENAI_API_KEY=sk-...
```

If the environment variable is set, you do not need to enter it in the UI each time.

---

## Download Formats

| Format | Library | Contents |
|---|---|---|
| PDF | ReportLab | Branded header, stats table, paragraph summary, bullet points, key terms, footer |
| Word (.docx) | python-docx | Styled headings, paragraph summary, bullet list, key terms section |
| Plain Text (.txt) | Built-in | Simple formatted text report with all sections |

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
- **Max upload size** — Currently limited to 16 MB per file.

---

## Future Improvements

- OCR support for scanned PDFs (Tesseract integration)
- Support for .docx and .txt file uploads
- Multi-document comparison mode
- User accounts and summary history
- Citation extraction and reference listing
- Language detection and multilingual support
- ROUGE score evaluation against human-written summaries

---

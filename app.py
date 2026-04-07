from flask import Flask, render_template, request, jsonify, send_file, Response
import os, json
from dotenv import load_dotenv, dotenv_values
from core.summarizer import summarize_text
from core.tfidf_summarizer import extract_keywords
from core.citations import extract_citations
from core.pdf_extractor import extract_text_from_pdf
from core.exporter import export_txt, export_docx, export_pdf

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(_env_path, override=True)

if os.environ.get('OPENAI_API_KEY'):
    print("[ScholarSum] OpenAI API key loaded — will use GPT-4o-mini.")
else:
    print("[ScholarSum] No OPENAI_API_KEY found — will use TF-IDF fallback.")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None  # No upload size limit

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api-status')
def api_status():
    if os.path.exists(_env_path):
        # Dev: read only from .env file so removing the key takes effect immediately.
        key = dotenv_values(_env_path).get('OPENAI_API_KEY', '').strip()
    else:
        # Production (Railway etc.): key is injected as a real env var.
        key = os.environ.get('OPENAI_API_KEY', '').strip()
    return jsonify({'connected': bool(key)})

@app.route('/summarize', methods=['POST'])
def summarize():
    text = ''
    error = None

    if 'pdf_file' in request.files and request.files['pdf_file'].filename != '':
        pdf_file = request.files['pdf_file']
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Please upload a valid PDF file.'}), 400
        filepath = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
        pdf_file.save(filepath)
        text, error = extract_text_from_pdf(filepath)
        try:
            os.remove(filepath)
        except Exception:
            pass
        if error:
            return jsonify({'error': error}), 400

    elif request.form.get('text_input', '').strip():
        text = request.form['text_input'].strip()
    else:
        return jsonify({'error': 'Please upload a PDF or paste some text.'}), 400

    if len(text.split()) < 50:
        return jsonify({'error': 'Text is too short to summarize (minimum 50 words).'}), 400

    try:
        ratio = int(request.form.get('summary_length', 20)) / 100
        ratio = max(0.05, min(ratio, 0.5))
    except ValueError:
        ratio = 0.20

    language = request.form.get('language', 'English').strip() or 'English'

    # Dev: sync os.environ from .env file in real time (handles key removal).
    # Production: os.environ is already set by the platform — leave it alone.
    if os.path.exists(_env_path):
        api_key = dotenv_values(_env_path).get('OPENAI_API_KEY', '').strip()
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        else:
            os.environ.pop('OPENAI_API_KEY', None)

    bullet_points, paragraph, sentence_count, method = summarize_text(text, ratio, language)
    keywords = extract_keywords(text, top_n=10)
    citations = extract_citations(text)

    return jsonify({
        'bullet_points': bullet_points,
        'paragraph': paragraph,
        'keywords': keywords,
        'citations': citations,
        'original_word_count': len(text.split()),
        'summary_word_count': len(paragraph.split()),
        'sentence_count': sentence_count,
        'method': method,
        'language': language,
    })


@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    fmt = data.get('format', 'txt')
    # Build filename from original source file, e.g. "Process.pdf" -> "Process_summarized"
    raw_name = data.get('source_filename', 'document')
    base = raw_name.rsplit('.', 1)[0] if '.' in raw_name else raw_name
    filename = base + '_summarized'
    bullet_points = data.get('bullet_points', [])
    paragraph = data.get('paragraph', '')
    keywords = data.get('keywords', [])
    original_word_count = data.get('original_word_count', 0)
    summary_word_count = data.get('summary_word_count', 0)

    if fmt == 'txt':
        content_txt = export_txt(bullet_points, paragraph, keywords, original_word_count, summary_word_count)
        return Response(
            content_txt,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={filename}.txt'}
        )
    elif fmt == 'docx':
        buf = export_docx(bullet_points, paragraph, keywords, original_word_count, summary_word_count)
        return send_file(
            buf,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=filename + '.docx'
        )
    elif fmt == 'pdf':
        buf = export_pdf(bullet_points, paragraph, keywords, original_word_count, summary_word_count)
        return send_file(
            buf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename + '.pdf'
        )
    else:
        return jsonify({'error': 'Unknown format'}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
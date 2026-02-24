from flask import Flask, render_template, request, jsonify, send_file, Response
import os, json
from summarizer import summarize_text, extract_keywords
from pdf_extractor import extract_text_from_pdf
from exporter import export_txt, export_docx, export_pdf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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

    api_key = request.form.get('api_key', '').strip()
    # Set or clear the key each request so it doesn't persist from a previous call
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    else:
        os.environ.pop('OPENAI_API_KEY', None)

    bullet_points, paragraph, sentence_count, method = summarize_text(text, ratio)
    keywords = extract_keywords(text, top_n=10)

    return jsonify({
        'bullet_points': bullet_points,
        'paragraph': paragraph,
        'keywords': keywords,
        'original_word_count': len(text.split()),
        'summary_word_count': len(paragraph.split()),
        'sentence_count': sentence_count,
        'method': method
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
    app.run(debug=False, host='127.0.0.1', port=5000)
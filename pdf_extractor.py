def extract_text_from_pdf(filepath):
    """
    Extract text from a PDF file using PyPDF2.
    Returns (text, error_message). If successful, error_message is None.
    """
    try:
        import PyPDF2
    except ImportError:
        return '', 'PyPDF2 is not installed. Run: pip install PyPDF2'

    try:
        text_parts = []
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) == 0:
                return '', 'The PDF appears to be empty.'
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = '\n'.join(text_parts).strip()

        if not full_text:
            return '', 'Could not extract text from this PDF. It may be scanned or image-based (OCR required).'

        return full_text, None

    except Exception as e:
        return '', f'Error reading PDF: {str(e)}'

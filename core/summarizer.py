from core.openai_summarizer import summarize_with_openai
from core.tfidf_summarizer import summarize_with_tfidf, extract_keywords
from core.citations import extract_citations


def summarize_text(text: str, ratio: float = 0.20, language: str = "English") -> tuple:
    """
    Try OpenAI first; fall back to TF-IDF if the API is unavailable or fails.
    Returns (bullet_points, paragraph, sentence_count, method_used).
    """
    try:
        bullets, paragraph, count = summarize_with_openai(text, ratio, language)
        return bullets, paragraph, count, "openai"
    except Exception as e:
        print(f"[OpenAI failed — using TF-IDF fallback]: {e}")
        bullets, paragraph, count = summarize_with_tfidf(text, ratio)
        return bullets, paragraph, count, "tfidf"

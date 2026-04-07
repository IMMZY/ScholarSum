import re
import math
import nltk
from collections import defaultdict

from core.text_cleaner import is_junk, clean_text, strip_references_section, preprocess_for_tfidf


def _ensure_nltk_resources():
    resources = [
        ('tokenizers/punkt',     'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords',    'stopwords'),
    ]
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)

_ensure_nltk_resources()

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words('english'))


# ── Tokenization helpers ───────────────────────────────────────────────────────

def get_sentences(text: str) -> list:
    return sent_tokenize(text)


def tokenize_words(sentence: str) -> list:
    tokens = word_tokenize(sentence.lower())
    return [t for t in tokens if t.isalpha() and t not in STOPWORDS and len(t) > 2]


# ── TF-IDF scoring ─────────────────────────────────────────────────────────────

def compute_tfidf(sentences: list) -> list:
    N = len(sentences)
    tokenized = [tokenize_words(s) for s in sentences]

    df = defaultdict(int)
    for tokens in tokenized:
        for word in set(tokens):
            df[word] += 1

    tfidf = []
    for tokens in tokenized:
        tf_scores = defaultdict(float)
        if not tokens:
            tfidf.append(tf_scores)
            continue
        token_count = len(tokens)
        freq = defaultdict(int)
        for t in tokens:
            freq[t] += 1
        for word, count in freq.items():
            tf  = count / token_count
            idf = math.log((N + 1) / (df[word] + 1)) + 1
            tf_scores[word] = tf * idf
        tfidf.append(tf_scores)
    return tfidf


def score_sentences(sentences: list, tfidf: list) -> list:
    """Score each sentence by TF-IDF weight with a positional boost."""
    n = len(sentences)
    scores = []
    for i, (sentence, tf_scores) in enumerate(zip(sentences, tfidf)):
        if not tf_scores:
            scores.append(0.0)
            continue
        base_score     = sum(tf_scores.values()) / max(len(tf_scores), 1)
        position_ratio = i / max(n - 1, 1)
        if position_ratio <= 0.10 or position_ratio >= 0.90:
            boost = 1.4
        elif position_ratio <= 0.20 or position_ratio >= 0.80:
            boost = 1.15
        else:
            boost = 1.0
        scores.append(base_score * boost)
    return scores


# ── Public API ─────────────────────────────────────────────────────────────────

def summarize_with_tfidf(text: str, ratio: float = 0.20) -> tuple:
    text = strip_references_section(text)
    text = preprocess_for_tfidf(text)
    text = clean_text(text)

    all_sentences   = get_sentences(text)
    clean_sentences = [(i, s) for i, s in enumerate(all_sentences) if not is_junk(s)]
    if not clean_sentences:
        return [], text[:500], 0

    _, sentences = zip(*clean_sentences)
    sentences = list(sentences)

    num_sentences = max(5, round(len(sentences) * ratio))
    num_sentences = min(num_sentences, 10)

    tfidf  = compute_tfidf(sentences)
    scores = score_sentences(sentences, tfidf)

    ranked   = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    selected = sorted(ranked[:num_sentences])

    bullet_points = [sentences[i] for i in selected]
    paragraph     = re.sub(r'\s+', ' ', ' '.join(bullet_points)).strip()
    return bullet_points, paragraph, len(bullet_points)


def extract_keywords(text: str, top_n: int = 10) -> list:
    text      = clean_text(text)
    sentences = [s for s in get_sentences(text) if not is_junk(s)]
    if not sentences:
        return []

    tfidf       = compute_tfidf(sentences)
    word_scores = defaultdict(float)
    for tf_scores in tfidf:
        for word, score in tf_scores.items():
            word_scores[word] += score

    sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    return [(word, round(score, 4)) for word, score in sorted_words[:top_n]]

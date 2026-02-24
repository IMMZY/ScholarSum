import re
import math
import os
import nltk
from collections import defaultdict

def _ensure_nltk_resources():
    resources = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords'),
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

JUNK_PATTERNS = [
    r'@',
    r'\.{3,}',
    r'http[s]?://',
    r'©|all rights reserved',
    r'^\s*\d+\s*$',
    r'[^\x00-\x7F]{3,}',
    r'\d{2,}\s*[●■□▪•]{2,}',
    r'^.{1,20}$',
    r'\w{25,}',
    r'(fig\.|table\s*\d|vol\.|pp\.|et al\.)',
    r'^\s*(abstract|references|bibliography|acknowledgements?|appendix)\s*$',
]
JUNK_RE = [re.compile(p, re.IGNORECASE) for p in JUNK_PATTERNS]


def is_junk(sentence):
    s = sentence.strip()
    for pattern in JUNK_RE:
        if pattern.search(s):
            return True
    words = [w for w in s.split() if w.isalpha()]
    # Too few real words
    if len(words) < 7:
        return True
    # Too many ALL CAPS words (headers/titles)
    caps_words = [w for w in words if w.isupper() and len(w) > 2]
    if len(caps_words) > len(words) * 0.5:
        return True
    # High ratio of numbers (data rows)
    numeric = [t for t in s.split() if re.match(r'^\d+[\.,]?\d*%?$', t)]
    if len(numeric) > len(s.split()) * 0.4:
        return True
    return False


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    return text.strip()


# ─────────────────────────────────────────────
#  OpenAI Summarizer (primary)
# ─────────────────────────────────────────────

def summarize_with_openai(text, ratio=0.20):
    """
    Uses gpt-4o-mini to generate bullet points and a paragraph summary.
    Returns (bullet_points, paragraph, sentence_count) or raises Exception.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise Exception("openai package not installed. Run: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise Exception("OPENAI_API_KEY not set.")

    client = OpenAI(api_key=api_key)

    word_count = len(text.split())
    # Truncate to ~12000 words to stay within token limits
    if word_count > 12000:
        text = ' '.join(text.split()[:12000])

    percent = int(ratio * 100)

    prompt = f"""You are an expert academic summarizer helping students understand research papers and textbooks.

Summarize the following academic document. The user has requested a {percent}% length summary.

Return your response in this EXACT format:

BULLET_POINTS:
- [key point 1]
- [key point 2]
(include AT LEAST 10-15 bullet points covering all major ideas, findings, and conclusions)

PARAGRAPH:
[A thorough, well-structured summary in flowing prose. Must be at least 4-6 sentences covering background, methodology, key findings, and conclusions with smooth transitions.]

Rules:
- Bullet points must be meaningful complete sentences — each capturing a distinct specific idea
- Cover ALL major sections: background, objectives, methods, results, conclusions
- The paragraph must be detailed enough that a student understands the paper without reading it
- Do NOT produce fewer than 10 bullet points regardless of document length
- Ignore metadata, author info, copyright notices, and table of contents
- Focus only on the actual academic content

DOCUMENT:
{text}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3500,
    )

    raw = response.choices[0].message.content.strip()

    # Parse bullet points
    bullet_points = []
    paragraph = ""

    if "BULLET_POINTS:" in raw and "PARAGRAPH:" in raw:
        parts = raw.split("PARAGRAPH:")
        bullet_section = parts[0].replace("BULLET_POINTS:", "").strip()
        paragraph = parts[1].strip()

        for line in bullet_section.split('\n'):
            line = line.strip().lstrip('-•*').strip()
            if line and len(line.split()) >= 4:
                bullet_points.append(line)
    else:
        # Fallback parse: split by newlines
        lines = [l.strip().lstrip('-•*').strip() for l in raw.split('\n') if l.strip()]
        bullet_points = [l for l in lines if len(l.split()) >= 4]
        paragraph = ' '.join(bullet_points)

    return bullet_points, paragraph, len(bullet_points)


# ─────────────────────────────────────────────
#  TF-IDF Summarizer (fallback)
# ─────────────────────────────────────────────

def get_sentences(text):
    return sent_tokenize(text)


def tokenize_words(sentence):
    tokens = word_tokenize(sentence.lower())
    return [t for t in tokens if t.isalpha() and t not in STOPWORDS and len(t) > 2]


def compute_tfidf(sentences):
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
            tf = count / token_count
            idf = math.log((N + 1) / (df[word] + 1)) + 1
            tf_scores[word] = tf * idf
        tfidf.append(tf_scores)
    return tfidf


def score_sentences(sentences, tfidf):
    n = len(sentences)
    scores = []
    for i, (sentence, tf_scores) in enumerate(zip(sentences, tfidf)):
        if not tf_scores:
            scores.append(0.0)
            continue
        base_score = sum(tf_scores.values()) / max(len(tf_scores), 1)
        position_ratio = i / max(n - 1, 1)
        if position_ratio <= 0.10 or position_ratio >= 0.90:
            positional_boost = 1.4
        elif position_ratio <= 0.20 or position_ratio >= 0.80:
            positional_boost = 1.15
        else:
            positional_boost = 1.0
        scores.append(base_score * positional_boost)
    return scores


def summarize_with_tfidf(text, ratio=0.20):
    text = clean_text(text)
    all_sentences = get_sentences(text)
    clean_sentences = [(i, s) for i, s in enumerate(all_sentences) if not is_junk(s)]
    if not clean_sentences:
        return [], text[:500], 0
    _, sentences = zip(*clean_sentences)
    sentences = list(sentences)
    # Cap between 5 and 10 bullet points regardless of ratio
    num_sentences = max(5, round(len(sentences) * ratio))
    num_sentences = min(num_sentences, 10)
    tfidf = compute_tfidf(sentences)
    scores = score_sentences(sentences, tfidf)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    selected = sorted(ranked[:num_sentences])
    bullet_points = [sentences[i] for i in selected]
    paragraph = re.sub(r'\s+', ' ', ' '.join(bullet_points)).strip()
    return bullet_points, paragraph, len(bullet_points)


# ─────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────

def summarize_text(text, ratio=0.20):
    """
    Try OpenAI first, fall back to TF-IDF if it fails.
    Returns (bullet_points, paragraph, sentence_count, method_used)
    """
    try:
        bullets, paragraph, count = summarize_with_openai(text, ratio)
        return bullets, paragraph, count, "openai"
    except Exception as e:
        print(f"[OpenAI failed, using TF-IDF fallback]: {e}")
        bullets, paragraph, count = summarize_with_tfidf(text, ratio)
        return bullets, paragraph, count, "tfidf"


def extract_keywords(text, top_n=10):
    text = clean_text(text)
    sentences = [s for s in get_sentences(text) if not is_junk(s)]
    if not sentences:
        return []
    tfidf = compute_tfidf(sentences)
    word_scores = defaultdict(float)
    for tf_scores in tfidf:
        for word, score in tf_scores.items():
            word_scores[word] += score
    sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    return [(word, round(score, 4)) for word, score in sorted_words[:top_n]]
import re

# ── Junk-detection patterns ────────────────────────────────────────────────────
JUNK_PATTERNS = [
    r'@',
    r'\.{3,}',
    r'http[s]?://|doi:|dx\.doi\.org',
    r'©|all rights reserved',
    r'^\s*\d+\s*$',
    r'[^\x00-\x7F]{3,}',
    r'\d{2,}\s*[●■□▪•]{2,}',
    r'^.{1,20}$',
    r'\w{25,}',
    r'(fig\.|table\s*\d|vol\.|pp\.|et al\.)',
    r'^\s*(abstract|references|bibliography|acknowledgements?|appendix)\s*$',
    r'^[\s\u2610\u2611\u2612\u25a0\u25a1\u25cb\u25cf\u2714\u2718\u25b6\u25c6□■○●◯✓✗✘▶◆]',
    r'^\s*[\"\u201c].{10,}[\"\u201d]\.?\s*$',
    r'\d+\s*\(\s*\d+\s*[-\u2013]\s*\d+\s*\)\s*,\s*\d+',
    r'\b1[89]\d{2}\s*[-\u2013]\s*\d{2,4}\.?\s*$',
    r'^[A-Z][a-z]+,\s+[A-Z]\..*\d{4}',
]
JUNK_RE = [re.compile(p, re.IGNORECASE) for p in JUNK_PATTERNS]

# Broad regex covering checkbox / box-drawing / misc symbol Unicode blocks
_SYMBOL_RE = re.compile(
    r'[\u2190-\u21ff'   # arrows
    r'\u2200-\u22ff'    # mathematical operators
    r'\u2300-\u23ff'    # misc technical
    r'\u2400-\u24ff'    # enclosed alphanumerics
    r'\u2500-\u257f'    # box drawing
    r'\u2580-\u259f'    # block elements
    r'\u25a0-\u25ff'    # geometric shapes (includes □ U+25A1)
    r'\u2600-\u26ff'    # misc symbols
    r'\u2700-\u27bf'    # dingbats
    r'\u2b00-\u2bff'    # misc symbols & arrows
    r']+'
)


def is_junk(sentence: str) -> bool:
    """Return True if the sentence is noise and should be excluded."""
    s = sentence.strip()
    for pattern in JUNK_RE:
        if pattern.search(s):
            return True
    words = [w for w in s.split() if w.isalpha()]
    if len(words) < 10:
        return True
    caps_words = [w for w in words if w.isupper() and len(w) > 2]
    if len(caps_words) > len(words) * 0.5:
        return True
    numeric = [t for t in s.split() if re.match(r'^\d+[\.,]?\d*%?$', t)]
    if len(numeric) > len(s.split()) * 0.4:
        return True
    return False


def clean_text(text: str) -> str:
    """Collapse whitespace and newlines into single spaces."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    return text.strip()


def strip_references_section(text: str) -> str:
    """Remove the references/bibliography section so it doesn't pollute TF-IDF."""
    match = re.search(
        r'(?im)^[ \t]*(References|Bibliography|Works\s+Cited|Literature\s+Cited)\s*$',
        text
    )
    if match:
        return text[:match.start()].strip()
    return text


def preprocess_for_tfidf(text: str) -> str:
    """
    Line-level cleanup before TF-IDF:
    - Drop lines that start with a non-ASCII symbol (checkboxes, bullets, etc.)
    - Strip inline symbol characters from remaining lines
    - Remove very short or digit-only lines
    """
    cleaned = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        first = line[0]
        if ord(first) > 127 and not first.isalpha():
            continue
        line = _SYMBOL_RE.sub('', line).strip()
        if not line or len(line) < 15 or re.match(r'^\d+$', line):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)

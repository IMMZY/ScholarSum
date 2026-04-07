import re


def extract_citations(text: str) -> list:
    """
    Extract citation/reference entries from academic text.
    Looks for a References section first, then falls back to inline citations.
    """
    # ── Strategy 1: numbered reference list after a section header ────────────
    ref_match = re.search(
        r'(?im)^[ \t]*(References|Bibliography|Works\s+Cited|Literature\s+Cited)\s*$',
        text
    )
    if ref_match:
        ref_text = text[ref_match.end():]
        entries  = re.findall(r'(?m)^\s*\[?\d+\]?\.?\s+(.{20,280})', ref_text)
        citations = [e.strip() for e in entries if len(e.split()) >= 4][:15]
        if citations:
            return citations

    # ── Strategy 2: inline (Author, Year) citations ───────────────────────────
    inline = re.findall(
        r'\(([A-Z][A-Za-z\-]+(?:\s+et\s+al\.)?(?:\s+&\s+[A-Z][a-z]+)?,?\s+\d{4}[^)]{0,60})\)',
        text
    )
    seen      = set()
    citations = []
    for c in inline:
        c = c.strip()
        if c not in seen and len(c) > 5:
            seen.add(c)
            citations.append(c)
        if len(citations) >= 10:
            break

    return citations[:15]

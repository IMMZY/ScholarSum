import os
from openai import OpenAI


def summarize_with_openai(text: str, ratio: float = 0.20, language: str = "English") -> tuple:
    """
    Uses GPT-4o-mini to generate bullet points and a paragraph summary.
    Returns (bullet_points, paragraph, sentence_count) or raises Exception.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise Exception("OPENAI_API_KEY not set.")

    client = OpenAI(api_key=api_key)

    # Truncate to ~12 000 words to stay within token limits
    words = text.split()
    if len(words) > 12000:
        text = ' '.join(words[:12000])

    percent          = int(ratio * 100)
    lang_instruction = (
        f"\nIMPORTANT: Write your ENTIRE response (bullet points and paragraph) in {language}."
        if language and language.lower() != "english"
        else ""
    )

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
- Focus only on the actual academic content{lang_instruction}

DOCUMENT:
{text}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3500,
    )

    raw = response.choices[0].message.content.strip()
    return _parse_response(raw)


def _parse_response(raw: str) -> tuple:
    """Parse the structured BULLET_POINTS / PARAGRAPH response from the model."""
    bullet_points = []
    paragraph     = ""

    if "BULLET_POINTS:" in raw and "PARAGRAPH:" in raw:
        parts          = raw.split("PARAGRAPH:")
        bullet_section = parts[0].replace("BULLET_POINTS:", "").strip()
        paragraph      = parts[1].strip()
        for line in bullet_section.split('\n'):
            line = line.strip().lstrip('-•*').strip()
            if line and len(line.split()) >= 4:
                bullet_points.append(line)
    else:
        # Fallback: treat every non-trivial line as a bullet
        lines         = [l.strip().lstrip('-•*').strip() for l in raw.split('\n') if l.strip()]
        bullet_points = [l for l in lines if len(l.split()) >= 4]
        paragraph     = ' '.join(bullet_points)

    return bullet_points, paragraph, len(bullet_points)

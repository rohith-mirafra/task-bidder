def parse_skills(text):
    """Split a free-text, comma/semicolon-separated skills string into a
    normalized set of lowercase tags, e.g. "Python, AWS; react" -> {"python", "aws", "react"}."""
    if not text:
        return set()
    return {s.strip().lower() for s in text.replace(";", ",").split(",") if s.strip()}

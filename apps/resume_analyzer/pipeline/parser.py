"""
Resume parser — Milestone 3.

Responsibility:
  Take raw PDF bytes, extract all text, then split that text into
  named sections (Contact, Skills, Education, Experience, Projects,
  Certifications) using header-detection heuristics.

Public API:
  parse(file_bytes: bytes, filename: str) -> dict
      Returns a ParsedResume dict on success.
      Raises ParseError if no text can be extracted.

Output shape:
  {
    "sections": {
      "contact":        "raw text block or null",
      "skills":         "raw text block or null",
      "education":      "raw text block or null",
      "experience":     "raw text block or null",
      "projects":       "raw text block or null",
      "certifications": "raw text block or null"
    },
    "raw_text":  "full extracted plain text",
    "metadata": {
      "filename":   "original filename",
      "page_count": 2,
      "word_count": 480
    }
  }
"""

import io
import re
import logging

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Section header patterns
# Each tuple: (section_key, compiled_regex)
# The regex matches a line that IS a section header for that section.
# Order matters — the first match wins for each line.
# ---------------------------------------------------------------------------
_SECTION_PATTERNS = [
    ('contact', re.compile(
        r'^\s*(contact(\s+info(rmation)?)?|personal\s+info(rmation)?|profile)\s*$',
        re.IGNORECASE,
    )),
    ('skills', re.compile(
        r'^\s*(technical\s+)?(skills?|competenc(y|ies)|technologies|tech\s+stack|tools)\s*$',
        re.IGNORECASE,
    )),
    ('education', re.compile(
        r'^\s*(education(al\s+background)?|academic\s+(background|qualifications?)|qualifications?)\s*$',
        re.IGNORECASE,
    )),
    ('experience', re.compile(
        r'^\s*(work\s+)?(experience|employment(\s+history)?|work\s+history|professional\s+(experience|background))\s*$',
        re.IGNORECASE,
    )),
    ('projects', re.compile(
        r'^\s*(projects?|personal\s+projects?|side\s+projects?|portfolio)\s*$',
        re.IGNORECASE,
    )),
    ('certifications', re.compile(
        r'^\s*(certifications?|certificates?|licenses?\s+&?\s+certifications?|accreditations?|credentials?)\s*$',
        re.IGNORECASE,
    )),
]

# Section keys in the order we want them in the output
_SECTION_KEYS = ['contact', 'skills', 'education', 'experience', 'projects', 'certifications']


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(file_bytes: bytes, filename: str) -> dict:
    """
    Parse a PDF resume.

    Parameters
    ----------
    file_bytes : raw bytes of the PDF file
    filename   : original filename (stored in metadata)

    Returns
    -------
    dict with keys: sections, raw_text, metadata

    Raises
    ------
    ParseError  if no readable text can be extracted
    """
    raw_text, page_count = _extract_text(file_bytes)

    if not raw_text or not raw_text.strip():
        raise ParseError("Unable to extract text from the provided file.")

    sections = _detect_sections(raw_text)
    word_count = len(raw_text.split())

    return {
        "sections": sections,
        "raw_text": raw_text,
        "metadata": {
            "filename": filename,
            "page_count": page_count,
            "word_count": word_count,
        },
    }


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def _extract_text(file_bytes: bytes) -> tuple[str, int]:
    """
    Extract all text from a PDF using pdfminer.six.

    Returns (raw_text, page_count).
    Raises ParseError on unrecoverable extraction failure.
    """
    try:
        # Count pages
        page_count = _count_pages(file_bytes)

        # Extract text
        output = io.StringIO()
        input_buf = io.BytesIO(file_bytes)
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5,
            detect_vertical=False,
        )
        extract_text_to_fp(input_buf, output, laparams=laparams, output_type='text', codec='utf-8')
        raw_text = output.getvalue()
        return raw_text, page_count

    except ParseError:
        raise
    except Exception as exc:
        logger.exception("pdfminer extraction failed: %s", exc)
        raise ParseError("Unable to extract text from the provided file.") from exc


def _count_pages(file_bytes: bytes) -> int:
    """Return the number of pages in the PDF."""
    try:
        buf = io.BytesIO(file_bytes)
        parser = PDFParser(buf)
        doc = PDFDocument(parser)
        return sum(1 for _ in PDFPage.create_pages(doc))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

def _detect_sections(raw_text: str) -> dict:
    """
    Split raw_text into named sections using header-line detection.

    Strategy:
    1. Split text into lines.
    2. Walk each line — if it matches a section header pattern, start
       collecting content under that section key.
    3. Content before the first recognised header goes to 'contact'
       (most resumes start with name/email/phone at the top).
    4. If a section header is never found, its value is None.

    Returns a dict with all six section keys.
    """
    sections: dict[str, list[str]] = {key: [] for key in _SECTION_KEYS}
    current_section: str | None = 'contact'  # assume top-of-resume = contact info

    lines = raw_text.splitlines()

    for line in lines:
        matched_section = _match_header(line)

        if matched_section:
            current_section = matched_section
            # Don't include the header line itself as content
            continue

        if current_section is not None:
            sections[current_section].append(line)

    # Convert lists → stripped strings; None if empty
    result = {}
    for key in _SECTION_KEYS:
        block = '\n'.join(sections[key]).strip()
        result[key] = block if block else None

    return result


def _match_header(line: str) -> str | None:
    """
    Return the section key if the line is a section header, else None.

    A line qualifies as a header when:
    - It matches one of the section patterns, AND
    - It is short (≤ 60 characters) — long lines are almost never headers
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return None

    for section_key, pattern in _SECTION_PATTERNS:
        if pattern.match(stripped):
            return section_key

    return None


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class ParseError(Exception):
    """Raised when the parser cannot extract readable text from a file."""
    pass

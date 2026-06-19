"""
Utility script to generate a minimal but real PDF fixture for parser tests.
Run once:  python apps/resume_analyzer/tests/fixtures/make_fixture.py
Outputs:   apps/resume_analyzer/tests/fixtures/sample_resume.pdf
"""

import pathlib
import textwrap


def make_pdf(text: str) -> bytes:
    """
    Build a minimal single-page PDF containing the given text.
    Uses only the Python stdlib — no external libraries needed.
    The output is a valid PDF 1.4 document that pdfminer can parse.
    """
    # Encode text lines as PDF content stream
    lines = text.split('\n')
    content_lines = ['BT', '/F1 11 Tf', '50 750 Td', '14 TL']
    for line in lines:
        # Escape parentheses and backslashes for PDF string syntax
        safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        content_lines.append(f'({safe}) Tj T*')
    content_lines.append('ET')
    content_stream = '\n'.join(content_lines)
    stream_bytes = content_stream.encode('latin-1', errors='replace')

    # Build PDF objects
    objects = []

    # obj 1: Catalog
    objects.append(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
    # obj 2: Pages
    objects.append(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
    # obj 3: Page
    objects.append(
        b'3 0 obj\n'
        b'<< /Type /Page /Parent 2 0 R\n'
        b'   /MediaBox [0 0 612 792]\n'
        b'   /Contents 4 0 R\n'
        b'   /Resources << /Font << /F1 5 0 R >> >> >>\n'
        b'endobj\n'
    )
    # obj 4: Content stream
    stream_len = len(stream_bytes)
    obj4 = (
        f'4 0 obj\n<< /Length {stream_len} >>\nstream\n'.encode()
        + stream_bytes
        + b'\nendstream\nendobj\n'
    )
    objects.append(obj4)
    # obj 5: Font
    objects.append(
        b'5 0 obj\n'
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n'
        b'endobj\n'
    )

    # Assemble PDF
    header = b'%PDF-1.4\n'
    body = b''
    offsets = []
    pos = len(header)
    for obj in objects:
        offsets.append(pos)
        body += obj
        pos += len(obj)

    # Cross-reference table
    xref_pos = len(header) + len(body)
    xref = f'xref\n0 {len(objects) + 1}\n'
    xref += '0000000000 65535 f \n'
    for off in offsets:
        xref += f'{off:010d} 00000 n \n'

    trailer = (
        f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n'
        f'startxref\n{xref_pos}\n%%EOF\n'
    )

    return header + body + xref.encode() + trailer.encode()


RESUME_TEXT = textwrap.dedent("""\
    John Smith
    john.smith@email.com | +1 555-0100 | linkedin.com/in/johnsmith

    Contact
    john.smith@email.com
    +1 555-0100
    New York, NY

    Skills
    Python, Django, Django REST Framework
    PostgreSQL, Supabase
    Git, Docker, Linux
    REST APIs, JWT Authentication

    Education
    Bachelor of Science in Computer Science
    New York University, 2019 - 2023
    GPA: 3.8 / 4.0

    Experience
    Software Engineer - Acme Corp (2023 - Present)
    Developed REST APIs using Django and PostgreSQL
    Reduced API response time by 40% through query optimisation
    Led migration of legacy monolith to modular Django apps

    Junior Developer - StartupXYZ (2022 - 2023)
    Built internal tooling with Python and Flask
    Wrote unit tests achieving 85% code coverage

    Projects
    Khan IntelliHub - Resume Analyzer
    AI-powered resume analysis platform built with Django REST Framework
    Implemented JWT authentication and Supabase Storage integration

    Personal Portfolio Website
    Designed and deployed a React + Vite SPA hosted on Vercel

    Certifications
    AWS Certified Developer - Associate (2024)
    Django REST Framework Advanced Course - Udemy (2023)
""")


if __name__ == '__main__':
    out_dir = pathlib.Path(__file__).parent
    out_path = out_dir / 'sample_resume.pdf'
    pdf_bytes = make_pdf(RESUME_TEXT)
    out_path.write_bytes(pdf_bytes)
    print(f'Written {len(pdf_bytes)} bytes to {out_path}')

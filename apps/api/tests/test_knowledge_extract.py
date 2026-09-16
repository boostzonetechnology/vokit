from __future__ import annotations

import pytest

from control_plane.agents.infrastructure.extract import extract_knowledge_text
from shared_kernel.errors import DomainError


def test_markdown_and_html_extract_text() -> None:
    markdown = extract_knowledge_text(
        filename="guide.md", content_type="text/markdown", data=b"# Hello cedar"
    )
    assert "Hello cedar" in markdown
    html = extract_knowledge_text(
        filename="page.html",
        content_type="text/html",
        data=b"<html><body><p>Hours 9-5</p></body></html>",
    )
    assert "Hours 9-5" in html


def test_pdf_extracts_visible_text() -> None:
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R"
        b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 55>>stream\n"
        b"BT /F1 12 Tf 10 100 Td (Hello cedar) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n"
        b"0000000101 00000 n \n0000000229 00000 n \n0000000334 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n406\n%%EOF"
    )
    text = extract_knowledge_text(filename="note.pdf", data=pdf)
    assert "Hello cedar" in text


def test_unsupported_and_empty_files_are_rejected() -> None:
    with pytest.raises(DomainError) as unsupported:
        extract_knowledge_text(filename="payload.exe", data=b"MZ")
    assert unsupported.value.code == "unsupported_knowledge_type"
    with pytest.raises(DomainError) as empty:
        extract_knowledge_text(filename="empty.md", data=b"   ")
    assert empty.value.code == "knowledge_extract_failed"

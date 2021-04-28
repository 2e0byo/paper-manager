from pathlib import Path

import pytest
from PyPDF2 import PdfFileReader

import manage_paper as mp

candidates = [
    ["test_data/strip_first_page_differing_sizes.pdf", 0],
    ["test_data/pdf.pdf", 0],
]


@pytest.mark.parametrize("paper,cover_page", candidates)
def test_strip_cover_page(paper, cover_page):
    pdf = PdfFileReader(Path(paper).open("rb"))
    pages = mp.find_cover_page(pdf)
    stripped = [pdf.getPageNumber(p) for p in pdf.pages if p not in pages]
    assert stripped == [cover_page]

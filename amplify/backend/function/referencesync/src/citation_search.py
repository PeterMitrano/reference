import io
from dataclasses import dataclass
from typing import List

import arxiv
import requests
from arxiv import HTTPError, UnexpectedEmptyPageError
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

from dropbox_utils import download_from_dropbox
from logging_utils import get_logger

logger = get_logger(__file__)
DEFAULT_CONFIDENCE_THRESHOLD = 0.5

TITLE_GUESS_MAX_LENGTH = 256


@dataclass
class TitleAuthor:
    title: str
    author: str


@dataclass
class CitationInfo:
    title: str
    authors: List[str]
    venue: str
    year: int
    confidence: float


NO_CITATION_INFO = CitationInfo(title='', authors=[], venue='', year=0, confidence=0.0)


def search_semantic_scholar(query: str):
    search_url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    params = {
        'query': query,
        'limit': 1,
        'fields': 'title,authors,venue,year',
    }
    res = requests.get(search_url, params)
    if not res.ok:
        logger.warn(f"Semantic scholar query failed {res.status_code}")
        logger.warn(res.text)
        return NO_CITATION_INFO

    query_res = res.json()
    if query_res['total'] == 0:
        return NO_CITATION_INFO

    first_paper_res = query_res['data'][0]
    return CitationInfo(
        title=first_paper_res['title'],
        authors=[author_info['name'] for author_info in first_paper_res['authors']],
        venue=first_paper_res['venue'],
        year=first_paper_res['year'],
        confidence=1.0,
    )


def search_arxiv(query_str):
    search = arxiv.Search(query=query_str, max_results=1)
    try:
        paper = next(search.results())
        return CitationInfo(
            title=paper.title,
            authors=paper.authors,
            venue=paper.journal_ref,
            year=paper.published.tm_year,
            confidence=1.0,
        )
    except (HTTPError, UnexpectedEmptyPageError):
        return NO_CITATION_INFO


def guess_arxiv_from_filename(name):
    arxiv_id = name.strip(".pdf").strip("/")
    search = arxiv.Search(id_list=[arxiv_id], max_results=1)
    results = search.results()
    try:
        paper = next(results)
        title = paper.title
        return CitationInfo(
            title=title,
            authors=[author.name for author in paper.authors],
            venue=paper.journal_ref,
            year=paper.published.tm_year,
            confidence=1.0,
        )
    except (HTTPError, UnexpectedEmptyPageError):
        return NO_CITATION_INFO


def guess_from_pdf_metadata(io_fp):
    parser = PDFParser(io_fp)
    doc = PDFDocument(parser)
    pdf_metadata = doc.info[0]

    return CitationInfo(
        title=pdf_metadata.get('Title', b'').decode("utf-8", errors='ignore'),
        authors=pdf_metadata.get('Author', b'').decode("utf-8", errors='ignore').split(" "),  # TODO: be smarter here
        venue='',
        year=0,
        confidence=0.2,
    )


def guess_from_NLP(inputs):
    return '', []


def extract_citation_info(dbx, file):
    file_data = download_from_dropbox(dbx, file.name)
    io_fp = io.BytesIO(file_data)

    def language_model_inputs():
        full_text = extract_text(io_fp, maxpages=1)  # feature to ML mode

        elements = []  # feature to ML mode
        for page_layout in extract_pages(io_fp, maxpages=1):
            for element in page_layout:
                if hasattr(element, 'get_text'):
                    text = element.get_text()
                else:
                    text = ''
                if hasattr(element, 'get_pts'):
                    pts = element.get_pts()
                else:
                    pts = ''
        return full_text, elements

    inputs = language_model_inputs()
    nlp_guess = guess_from_NLP(inputs)

    guesses = [
        guess_from_pdf_metadata(io_fp),
        guess_arxiv_from_filename(file.name),
        nlp_guess,
    ]

    guess: CitationInfo
    for guess in guesses:
        query_strings = [
            f"{guess.title} {', '.join(guess.authors)} {guess.year} {guess.venue}",
            f"{guess.title} {', '.join(guess.authors)} {guess.year}",
            f"{guess.title} {', '.join(guess.authors)}",
            f"{guess.title}",
        ]
        for query_string in query_strings:
            ss_citation_info = search_semantic_scholar(query_string)
            arxiv_citation_info = search_arxiv(query_string)

    raise NotImplemented("still need to return")

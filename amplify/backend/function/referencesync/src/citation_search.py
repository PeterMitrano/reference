import io
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List

import arxiv
import editdistance
import numpy as np
import openai
import requests
from arxiv import HTTPError, UnexpectedEmptyPageError
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

from dropbox_utils import download_from_dropbox
from ga import GA
from logging_utils import get_logger

logger = get_logger(__file__)
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
MAX_QUERY_SIZE = 256
MAX_FULL_TEXT = 512
MAX_ELEMENTS = 6


@dataclass
class Citation:
    title: str
    authors: List[str]
    venue: str
    year: int
    confidence: float


NO_CITATION_INFO = Citation(title='', authors=[], venue='', year=0, confidence=0.0)


def titlecase(s):
    """ taken from https://www.pythontutorial.net/python-string-methods/python-titlecase/ """
    return re.sub("[A-Za-z]+('[A-Za-z]+)?",
                  lambda word: word.group(0).capitalize(),
                  s)


def strify(x):
    return x if x is not None else ''


def intify(x):
    try:
        return int(x) if x is not None else 0
    except ValueError:
        return 0


@lru_cache
def search_semantic_scholar(query: str):
    search_url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    params = {
        'query': query,
        'limit': 3,
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
    return Citation(
        title=strify(first_paper_res['title']),
        authors=[author['name'] for author in first_paper_res['authors']],
        venue=strify(first_paper_res['venue']),
        year=intify(first_paper_res['year']),
        confidence=1.0,
    )


def query_arxiv(query='', id_list=None):
    if id_list is None:
        id_list = []
    search = arxiv.Search(query=query, id_list=id_list, max_results=3)
    try:
        paper = next(search.results())
        return Citation(
            title=strify(paper.title),
            authors=strify([a.name for a in paper.authors]),
            venue=strify(paper.journal_ref),
            year=intify(paper.published.year),
            confidence=1.0,
        )
    except (HTTPError, UnexpectedEmptyPageError, StopIteration):
        return NO_CITATION_INFO


@lru_cache
def search_arxiv(query_str):
    return query_arxiv(query=query_str)


def guess_arxiv_from_filename(name):
    arxiv_id = name.strip(".pdf").strip("/.-")
    if re.fullmatch(r'[0-9]+.[0-9]+', arxiv_id):
        return query_arxiv(id_list=[arxiv_id])
    return NO_CITATION_INFO


def guess_from_pdf_metadata(pdf_fp):
    parser = PDFParser(pdf_fp)
    doc = PDFDocument(parser)
    pdf_metadata = doc.info[0]

    # FIXME: utf-8 is totally unacceptable
    return Citation(
        title=pdf_metadata.get('Title', b'').decode("utf-8", errors='ignore'),
        authors=pdf_metadata.get('Author', b'').decode("utf-8", errors='ignore').split(" "),  # TODO: be smarter here
        venue='',
        year=0,
        confidence=0.2,
    )


def format_element_for_gpt(element_idx, x):
    # x[text, bbox, w, h]
    text, _, w, h = x
    text = text.strip(" \n").replace('\n', '')
    return f'{element_idx}:\n\tTEXT: {text}\n\tW: {w}, H: {h}'


def format_inputs_for_gpt(full_text, elements):
    elements_str = '\n'.join([format_element_for_gpt(i, x) for i, x in enumerate(elements)])
    return '\n'.join([
        f"Full Text:",
        full_text.strip(" \n").replace("\n", " "),
        "The title is",
        # f"ELEMENTS:",
        # elements_str
    ])


def make_gpt_prompt(pdf_fp):
    full_text = extract_text(pdf_fp, maxpages=1)
    full_text = full_text[:MAX_FULL_TEXT]

    elements = []
    for page_layout in extract_pages(pdf_fp, maxpages=1):
        if len(elements) >= MAX_ELEMENTS:
            break
        for element in page_layout:
            if hasattr(element, 'get_text'):
                text = element.get_text()
            else:
                text = ''
            bbox = [str(int(x)) for x in element.bbox]
            w = str(int(element.width))
            h = str(int(element.height))
            elements.append([text, bbox, w, h])
    inputs = format_inputs_for_gpt(full_text, elements)
    return inputs


def guess_from_nlp(pdf_fp, n_completions):
    prompt = make_gpt_prompt(pdf_fp)
    completion = openai.Completion.create(engine="babbage-instruct-beta", prompt=prompt, max_tokens=20, n=n_completions)

    guesses = []
    for choice in completion['choices']:
        title = choice['text'].strip("\n ")
        if "\"" in title:
            title = re.sub(r"^.*?\"", "\"", title)
            m = re.findall(r"([^\"]+)", title, flags=re.MULTILINE)
            title = m[0]
        else:
            title = title.split("\n")[0]
        title = titlecase(title)
        guess = Citation(
            title=title,
            authors=[],
            venue='',
            year=0,
            confidence=0.1,
        )
        guesses.append(guess)
    return guesses


def search_online_databases(citation):
    query_string = f"{citation.title}"
    query_string = query_string[:MAX_QUERY_SIZE]
    arxiv_citation = search_arxiv(query_string)
    ss_citation = search_semantic_scholar(query_string)

    return [arxiv_citation, ss_citation]


class CitationGA(GA):

    def __init__(self, filename, pdf_fp, population_size=10):
        super().__init__()
        self.population_size = population_size
        self.filename = filename
        self.pdf_fp = pdf_fp

    def initialize(self):
        nlp_guess = guess_from_nlp(self.pdf_fp, n_completions=2)

        population = [
            guess_from_pdf_metadata(self.pdf_fp),
            guess_arxiv_from_filename(self.filename),
        ]
        population += nlp_guess

        population = self.rng.choice(population, self.population_size)
        return population

    def cost(self, citation: Citation):
        # one way to see if a citation is good is to use it to search a database.
        # If you don't get a result, that's a bad sign and deserves high cost. If you do, then the distance
        # of that result to the citation used for querying can be used as cost
        online_citations = search_online_databases(citation)

        all_costs = []
        for online_citation in online_citations:
            if online_citation == NO_CITATION_INFO:
                continue
            field_costs = [
                editdistance.eval(citation.title, online_citation.title),
                editdistance.eval(citation.venue, online_citation.venue),
                np.abs(citation.year - online_citation.year),
            ]
            authors_costs = [editdistance.eval(a1, a2) for a1, a2 in zip(citation.authors, online_citation.authors)]
            field_costs += authors_costs
            cost = sum(field_costs)
            all_costs.append(cost)
        return np.min(all_costs)

    def mutate(self, citation: Citation):
        # To mutate, we simply perform crossover with search results
        online_citations = search_online_databases(citation)
        valid_online_citations = list(filter(lambda c: c != NO_CITATION_INFO, online_citations))
        sampled_online_citation = self.rng.choice(valid_online_citations)
        if sampled_online_citation is not None:
            return self.crossover(citation, sampled_online_citation)
        return citation

    def crossover(self, citation1: Citation, citation2: Citation):
        # randomly inherit each field from parents
        keep_from_1 = (self.rng.rand(4) > 0.5)
        output = Citation(
            title=(citation1.title if keep_from_1[0] else citation2.title),
            authors=(citation1.authors if keep_from_1[1] else citation2.authors),
            venue=(citation1.venue if keep_from_1[2] else citation2.venue),
            year=(citation1.year if keep_from_1[3] else citation2.year),
            confidence=(citation1.confidence + citation2.confidence) / 2,
        )
        return output


def extract_citation(dbx, file):
    file_data = download_from_dropbox(dbx, file.name)
    pdf_fp = io.BytesIO(file_data)

    ga = CitationGA(filename=file.name, pdf_fp=pdf_fp)

    return ga.opt(generations=4)

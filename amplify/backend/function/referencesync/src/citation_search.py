import io
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import List

import arxiv
import numpy as np
import openai
import requests
from Levenshtein import distance
from arxiv import HTTPError, UnexpectedEmptyPageError
from fuzzywuzzy import fuzz
from pdfminer.high_level import extract_text
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

from dropbox_utils import download_from_dropbox
from ga import GA
from logging_utils import get_logger


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


logger = get_logger(__file__)
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
MAX_QUERY_SIZE = 256
MAX_FULL_TEXT = 512
MAX_ELEMENTS = 6
CURRENT_YEAR = intify(datetime.now().strftime('%Y'))
YEAR_WEIGHT = 0.1


@dataclass
class Citation:
    title: str
    authors: List[str]
    venue: str
    year: int
    confidence: float

    def __repr__(self):
        author_str = ','.join(self.authors) if len(self.authors) > 0 else 'NA'
        return f"<{self.title}: {author_str}, {self.year}@{self.venue}>"


NO_CITATION_INFO = Citation(title='', authors=[], venue='', year=CURRENT_YEAR, confidence=0.0)


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
        year=CURRENT_YEAR,
        confidence=0.2,
    )


def format_element_for_gpt(element_idx, x):
    # x[text, bbox, w, h]
    text, _, w, h = x
    text = text.strip(" \n").replace('\n', '')
    return f'{element_idx}:\n\tTEXT: {text}\n\tW: {w}, H: {h}'


def format_inputs_for_gpt(full_text, gpt_question):
    return '\n'.join([
        f"Full Text:",
        full_text.strip(" \n").replace("\n", " "),
        gpt_question + ':',
    ])


def make_gpt_prompt(full_text, gpt_question):
    prompt = format_inputs_for_gpt(full_text, gpt_question)
    return prompt


def authors_from_gpt_choice(choice):
    authors = choice['text'].strip("\n ")
    authors = authors.split(".")[0].split("\n")[0]
    authors = authors.split(",")
    authors = [author.strip(" \n\t,:\"\'") for author in authors]
    return authors


def title_from_gpt_choice(choice):
    title = choice['text'].strip("\n ")
    if "\"" in title:
        title = re.sub(r"^.*?\"", "\"", title)
        m = re.findall(r"([^\"]+)", title, flags=re.MULTILINE)
        title = m[0]
    else:
        title = title.split("\n")[0]
    title = titlecase(title).strip(".'\"")
    return title


def guess_from_nlp(pdf_fp, n_completions):
    guess_title_prompt = make_gpt_prompt(pdf_fp, gpt_question="The title is")
    title_completion = openai.Completion.create(engine="babbage-instruct-beta",
                                                prompt=guess_title_prompt,
                                                max_tokens=20,
                                                n=n_completions)
    guess_authors_prompt = make_gpt_prompt(pdf_fp, gpt_question="The author's names are:")
    authors_completion = openai.Completion.create(engine="babbage-instruct-beta",
                                                  prompt=guess_authors_prompt,
                                                  max_tokens=32,
                                                  n=n_completions)

    choices = zip(title_completion['choices'], authors_completion['choices'])
    guesses = []
    for title_completion_choice, authors_completion_choice in choices:
        title = title_from_gpt_choice(title_completion_choice)
        authors = authors_from_gpt_choice(authors_completion_choice)
        guess = Citation(
            title=title,
            authors=authors,
            venue='',
            year=CURRENT_YEAR,
            confidence=0.1,
        )
        guesses.append(guess)

    return guesses


def search_online_databases(citation):
    if len(citation.title) == 0:
        return [NO_CITATION_INFO]

    query_string = f"{citation.title}"
    query_string = query_string[:MAX_QUERY_SIZE]
    arxiv_citation = search_arxiv(query_string)
    ss_citation = search_semantic_scholar(query_string)

    return np.array([arxiv_citation, ss_citation])


def venue_cost(venue, online_venue):
    if len(online_venue) == 0 and len(venue) == 0:
        return 100
    elif len(online_venue) == 0:
        return 0
    else:
        return distance(venue, online_venue)


def authors_distance(authors, online_authors):
    num_authors_mismatch = abs(len(authors) - len(online_authors))
    authors_costs = sum([distance(a1, a2) for a1, a2 in zip(authors, online_authors)])
    return authors_costs + num_authors_mismatch


def online_search_cost(citation):
    # one way to see if a citation is good is to use it to search a database.
    # If you don't get a result, that's a bad sign and deserves high cost. If you do, then the distance
    # of that result to the citation used for querying can be used as cost
    all_online_citations = search_online_databases(citation)
    valid_online_citations = list(filter(lambda c: c != NO_CITATION_INFO, all_online_citations))
    if np.all(valid_online_citations == NO_CITATION_INFO) or len(valid_online_citations) == 0:
        return 100000

    all_costs = []
    for online_citation in valid_online_citations:
        field_costs = [
            distance(citation.title, online_citation.title),
            authors_distance(citation.authors, online_citation.authors),
            venue_cost(citation.venue, online_citation.venue),
            np.abs(citation.year - online_citation.year) * YEAR_WEIGHT,
            # cost for empty venue. Helpful since sometimes online search has empty venue too
            (10 if len(citation.venue) == 0 else 0),
        ]
        cost = sum(field_costs)
        all_costs.append(cost)
    return np.min(all_costs)


def dist_to_original_doct(citation, full_text):
    d = 100 - fuzz.partial_ratio(citation.title.lower(), full_text.lower())
    return d


class CitationGA(GA):

    def __init__(self, filename, pdf_fp, population_size=10):
        super().__init__()
        self.population_size = population_size
        self.filename = filename
        self.pdf_fp = pdf_fp
        self.full_text = extract_text(pdf_fp, maxpages=1)[:MAX_FULL_TEXT]

    def initialize(self):
        nlp_guess = guess_from_nlp(self.full_text, n_completions=3)

        population = [
            guess_from_pdf_metadata(self.pdf_fp),
            guess_arxiv_from_filename(self.filename),
        ]
        population += nlp_guess

        population = self.rng.choice(population, self.population_size)
        return population

    def cost(self, citation: Citation):
        return online_search_cost(citation) + dist_to_original_doct(citation, self.full_text)

    def mutate(self, citation: Citation):
        # To mutate, we simply perform crossover with search results
        online_citations = search_online_databases(citation)
        valid_online_citations = list(filter(lambda c: c != NO_CITATION_INFO, online_citations))

        if len(valid_online_citations) == 0:
            return citation

        sampled_online_citation = self.rng.choice(valid_online_citations)

        return self.crossover(citation, sampled_online_citation)

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


def standardize_venue(venue):
    print("TODO!!!")
    return venue


def extract_citation(dbx, file):
    file_data = download_from_dropbox(dbx, file.name)
    pdf_fp = io.BytesIO(file_data)

    ga = CitationGA(filename=file.name, pdf_fp=pdf_fp, population_size=20)

    best_citation = ga.opt(generations=4)
    best_citation.title = titlecase(best_citation.title)
    best_citation.venue = standardize_venue(best_citation.venue)

    return best_citation

from dataclasses import dataclass
from typing import List

import requests

from logging_utils import get_logger
from pdf import extract_standardized_metadata

logger = get_logger(__file__)
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


@dataclass
class CitationInfo:
    title: str
    authors: List[str]
    venue: str
    year: int
    confidence: float


NO_CITATION_INFO = CitationInfo(title='', authors=[], venue='', year=0, confidence=0.0)


def search_semantic_scholar_with_query(query):
    search_url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    params = {
        'query': query,
        # 'offset': offset,
        'limit': 1,
        'fields': 'title,authors,venue,year',
    }
    res = requests.get(search_url, params)
    if not res.ok:
        logger.warn("Semantic scholar query failed")
        logger.warn(res.text)
        return None
    return res


def search_for_citation_info(title, author):
    query_res = search_semantic_scholar(title, author)
    if query_res is None:
        return NO_CITATION_INFO

    first_paper_res = query_res['data'][0]

    title = first_paper_res['title']

    # TODO: a better way to get author names in a "first, initial, last" structure
    # for author_info in first_paper_res['authors']:
    #     author_info['authorId']
    #     res = requests.get(f"{paper_url}/{}/authors", params)

    authors = [author_info['name'] for author_info in first_paper_res['authors']]
    venue = first_paper_res['venue']
    year = first_paper_res['year']

    return CitationInfo(
        title=title,
        authors=authors,
        venue=venue,
        year=year,
        confidence=1.0,
    )


def search_semantic_scholar(title, author):
    if title == '' and author == '':
        logger.warn("No title or author")
        return None

    res = search_semantic_scholar_with_query(title + ' ' + author)
    if res is None:
        return None

    query_res = res.json()
    if query_res['total'] == 0:
        # first retry without the author, sometimes that helps
        res = search_semantic_scholar_with_query(title)
        if res is None:
            return None

        query_res = res.json()
        if query_res['total'] == 0:
            return None

    return query_res


def extract_citation_info(dbx, file):
    # the general architecture could be to first try to extract pdf metadata
    # then also try to extract text from PDF and use that
    # then use the file name (cites like arxiv have a reliable naming policy)
    # then we need to somehow combine all of that information into a series of queries to semantic scholar
    # then we need to rank the results and choose the best one

    # I'd like to train this system from data
    pdf_metadata = extract_standardized_metadata(dbx, file)
    if pdf_metadata is None:
        return NO_CITATION_INFO
    # NOTE: we need a fallback for when the title and author are blank!
    #  perhaps take in a whole slew of features here and use ML to determine title and author,
    #  then do semantic scholar search?
    citation_info = search_for_citation_info(pdf_metadata.title, pdf_metadata.author)
    return citation_info

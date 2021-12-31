from dataclasses import dataclass
from typing import List

import requests

from pdf import extract_standardized_metadata


@dataclass
class CitationInfo:
    title: str
    authors: List[str]
    venue: str
    year: str


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
        print(res.status_code)
        print(res.text)
        return None
    return res


def search_for_citation_info(title, author):
    query_res = search_semantic_scholar(title, author)
    if query_res is None:
        return None

    first_paper_res = query_res['data'][0]

    title = first_paper_res['title']

    # TODO: a better way to get author names in a "first, initial, last" structure
    # for author_info in first_paper_res['authors']:
    #     author_info['authorId']
    #     res = requests.get(f"{paper_url}/{}/authors", params)

    authors = [author_info['name'] for author_info in first_paper_res['authors']]
    venue = first_paper_res['venue']
    year = str(first_paper_res['year'])

    return CitationInfo(
        title=title,
        authors=authors,
        venue=venue,
        year=year,
    )


def search_semantic_scholar(title, author):
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
    pdf_metadata = extract_standardized_metadata(dbx, file)
    if pdf_metadata is None:
        return None
    citation_info = search_for_citation_info(pdf_metadata.title, pdf_metadata.author)
    return citation_info

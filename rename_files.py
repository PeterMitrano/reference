import io
import pathlib
import re
from dataclasses import dataclass
from typing import Optional, List

import requests
from dropbox import Dropbox
from dropbox.exceptions import HttpError
from dropbox.files import FileMetadata
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser


@dataclass
class StandardizedPDFMetadata:
    title: Optional[str] = None
    author: Optional[str] = None


@dataclass
class CitationInfo:
    title: str
    authors: List[str]
    venue: str
    year: str


def set_standardized(standardized_metadata: StandardizedPDFMetadata, k: str, v):
    k = k.lower()
    if k in ['title']:
        standardized_metadata.title = v
    if k in ['author']:
        standardized_metadata.author = v


def extract_metadata(dbx, file):
    file_data = download(dbx, file.name)
    io_fp = io.BytesIO(file_data)
    parser = PDFParser(io_fp)
    doc = PDFDocument(parser)
    metadata = doc.info[0]
    return metadata


def extract_standardized_metadata(dbx, file):
    metadata = extract_metadata(dbx, file)
    standardized_metadata = StandardizedPDFMetadata()
    for k, v in metadata.items():
        v = v.decode("utf-8")
        set_standardized(standardized_metadata, k, v)
    return standardized_metadata


def search_for_citation_info(title, author):
    search_url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    paper_url = 'https://api.semanticscholar.org/graph/v1/paper/'
    params = {
        'query': title + ' ' + author,
        # 'offset': offset,
        'limit': 1,
        'fields': 'title,authors,venue,year',
    }
    res = requests.get(search_url, params)
    if not res.ok:
        raise RuntimeError("bad request")
    query_res = res.json()
    if query_res['total'] == 0:
        raise RuntimeError("no results")
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
    )


def extract_citation_info(dbx, file):
    pdf_metadata = extract_standardized_metadata(dbx, file)
    citation_info = search_for_citation_info(pdf_metadata.title, pdf_metadata.author)
    return citation_info


def shorten_title(title: str):
    title = title.lower()
    pre_title = title.split(":")[0]
    pre_title.replace(" ", "_")
    words_to_remove = ['the', 'a', 'an', 'and', 'is', 'of', 'if', 'to', 'in', 'on']
    for word in words_to_remove:
        pre_title = pre_title.replace(f"{word} ", " ")
    short_title = pre_title.strip(" ")
    re.sub(r"[0-9,-,',\",\(,\)]+", '', short_title)
    return short_title


def extract_parts(dbx, file: FileMetadata):
    citation_info = extract_citation_info(dbx, file)
    short_title = shorten_title(citation_info.title)
    parts = {
        'short_title': short_title,
        'first_author_last_name': citation_info.authors[0],
        'year': citation_info,
    }
    return parts


def main():
    token = "_-BQxQRs7kYAAAAAAAAAAcMfNPAFq-03uvvurPr4jaJGRsovsGRtoqnwLItC5nEo"

    with Dropbox(oauth2_access_token=token) as dbx:
        res = dbx.files_list_folder('')
        new_paths = []
        for file in res.entries:
            path = pathlib.Path(file.name)
            if isinstance(file, FileMetadata):
                if path.suffix == '.pdf':
                    part_names = [
                        'short_title',
                        'first_author_last_name',
                        'year',
                    ]
                    parts = extract_parts(dbx, file)
                    parts = [parts[part_name] for part_name in part_names]
                    new_path = '_'.join(parts)
                    # rename the file to new_path
                    new_paths.append(new_path)
                else:
                    print(f"Skipping non-PDF file {path}")
            else:
                print(f"Skipping non-file {path}")
        dbx.files_move_batch_v2(new_paths)


def download(dbx, path):
    try:
        md, res = dbx.files_download('/' + path)
    except HttpError as err:
        print('*** HTTP error', err)
        return None
    data = res.content
    return data


if __name__ == '__main__':
    main()

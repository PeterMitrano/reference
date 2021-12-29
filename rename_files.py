import io
import pathlib
import re
from dataclasses import dataclass
from typing import List

import requests
from dropbox import Dropbox
from dropbox.exceptions import HttpError
from dropbox.files import FileMetadata, RelocationPath
from pdfminer.high_level import extract_text
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

TITLE_GUESS_MAX_LENGTH = 256


@dataclass
class StandardizedPDFMetadata:
    title: str
    author: str


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


def extract_standardized_metadata(dbx, file):
    file_data = download(dbx, file.name)
    io_fp = io.BytesIO(file_data)
    parser = PDFParser(io_fp)
    doc = PDFDocument(parser)
    metadata = doc.info[0]

    if 'Title' in metadata and 'Author' in metadata:
        return StandardizedPDFMetadata(metadata['Title'].decode("utf-8"), metadata['Author'].decode("utf-8"))
    elif 'Title' in metadata:
        return StandardizedPDFMetadata(metadata['Title'].decode("utf-8"), '')
    else:
        full_text = extract_text(io_fp)
        title_guess_from_text = full_text.split('\n')[0]
        title_guess_from_text = title_guess_from_text[:TITLE_GUESS_MAX_LENGTH]

        return StandardizedPDFMetadata(title_guess_from_text, '')


def search_for_citation_info(title, author):
    query = title + ' ' + author
    res = search_semantic_scholar(query)
    if res is None:
        return None

    query_res = res.json()
    if query_res['total'] == 0:
        # first retry without the author, sometimes that helps
        res = search_semantic_scholar(title)
        query_res = res.json()
        if query_res['total'] == 0:
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


def search_semantic_scholar(query):
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


def extract_citation_info(dbx, file):
    pdf_metadata = extract_standardized_metadata(dbx, file)
    if pdf_metadata is None:
        return None
    citation_info = search_for_citation_info(pdf_metadata.title, pdf_metadata.author)
    return citation_info


def shorten_title(title: str):
    title = title.lower()
    pre_title = title.split(":")[0]
    pre_title.replace(" ", "_")
    words_to_remove = ['the', 'a', 'an', 'and', 'is', 'of', 'if', 'to', 'in', 'on']
    for word in words_to_remove:
        pre_title = pre_title.replace(f" {word} ", " ")
    short_title = pre_title.strip(" ")
    short_title = re.sub(r"[0-9,-,',\",\(,\)]+", '', short_title)
    short_title = short_title.replace("  ", " ")
    return short_title


def extract_parts(dbx, file: FileMetadata):
    citation_info = extract_citation_info(dbx, file)
    if citation_info is None:
        return None
    short_title = shorten_title(citation_info.title)
    if len(citation_info.authors) == 0:
        first_author_last_name = ''
    else:
        first_author_last_name = citation_info.authors[0]

    parts = {
        'short_title': short_title,
        'first_author_last_name': first_author_last_name,
        'year': citation_info.year,
    }

    return parts


def main():
    token = "_-BQxQRs7kYAAAAAAAAAAcMfNPAFq-03uvvurPr4jaJGRsovsGRtoqnwLItC5nEo"

    with Dropbox(oauth2_access_token=token) as dbx:
        res = dbx.files_list_folder('')
        relocation_paths = []
        for file in res.entries[:5]:
            path = pathlib.Path(file.name)
            if isinstance(file, FileMetadata):
                if path.suffix == '.pdf':
                    part_names = [
                        'short_title',
                        'first_author_last_name',
                        'year',
                    ]
                    parts = extract_parts(dbx, file)
                    if parts is None:
                        print(f"Couldn't find info for {file.name}, skipping")
                        continue
                    parts = [parts[part_name] for part_name in part_names]
                    new_path = '/' + '_'.join(parts) + '.pdf'
                    new_path = new_path.replace(" ", "-")
                    # rename the file to new_path
                    print(f"{file.path_display} -> {new_path}")
                    relocation_path = RelocationPath(from_path=file.path_display, to_path=new_path)
                    relocation_paths.append(relocation_path)
                else:
                    print(f"Skipping non-PDF file {path}")
            else:
                print(f"Skipping non-file {path}")
        dbx.files_move_batch_v2(relocation_paths)


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

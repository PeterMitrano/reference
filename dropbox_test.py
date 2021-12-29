import io
import pathlib
from dataclasses import dataclass
from typing import Optional

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
    url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    params = {
        'query': title + ' ' + author,
        # 'offset': offset,
        'limit': 1,
        'fields': 'title,authors',
    }
    res = requests.get(url, params)
    if not res.ok:
        raise RuntimeError("bad request")
    query_res = res.json()
    if query_res['total'] == 0:
        raise RuntimeError("no results")
    query_res['data'][0]
    pass


def extract_citation_info(dbx, file):
    pdf_metadata = extract_standardized_metadata(dbx, file)
    citation_info = search_for_citation_info(pdf_metadata.title, pdf_metadata.author)
    return citation_info


def extract_part(dbx, file: FileMetadata, part_name: str):
    metadata = extract_citation_info(dbx, file)
    return metadata[part_name]


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
                    parts = [extract_part(dbx, file, part_name) for part_name in part_names]
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

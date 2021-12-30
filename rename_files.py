import io

import sqlite3
from sqlite3 import Error
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
    file_data = download_from_dropbox(dbx, file.name)
    io_fp = io.BytesIO(file_data)
    parser = PDFParser(io_fp)
    doc = PDFDocument(parser)
    metadata = doc.info[0]

    if 'Title' in metadata and 'Author' in metadata:
        title = metadata['Title'].decode("utf-8", errors='ignore')
        authors = metadata['Author'].decode("utf-8", errors='ignore')
        return StandardizedPDFMetadata(title, authors)
    elif 'Title' in metadata:
        title = metadata['Title'].decode("utf-8", errors='ignore')
        return StandardizedPDFMetadata(title, '')
    else:
        full_text = extract_text(io_fp)
        title_guess_from_text = full_text.split('\n')[0]
        title_guess_from_text = title_guess_from_text[:TITLE_GUESS_MAX_LENGTH]

        return StandardizedPDFMetadata(title_guess_from_text, '')


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


def extract_citation_info(dbx, file):
    pdf_metadata = extract_standardized_metadata(dbx, file)
    if pdf_metadata is None:
        return None
    citation_info = search_for_citation_info(pdf_metadata.title, pdf_metadata.author)
    return citation_info


def download_from_dropbox(dbx, path):
    try:
        md, res = dbx.files_download('/' + path)
    except HttpError as err:
        print('*** HTTP error', err)
        return None
    data = res.content
    return data


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


def extract_parts_for_renaming(citation_info):
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


def update_papers_table(citations_info, oauth_token):
    # FIXME: this will create duplicates
    conn = create_connection()
    cur = conn.cursor()
    columns = ['filename', 'oauth_token', 'title', 'authors', 'venue', 'year']
    values_strs = []
    for file, citation_info in citations_info:
        authors_str = ' '.join(citation_info.authors)
        values = [file.path_display, oauth_token, citation_info.title, authors_str, citation_info.venue,
                  citation_info.year]
        values_str = ','.join([f"\"{v}\"" for v in values])
        values_strs.append(f"({values_str})")
    insert_sql = f"INSERT INTO papers ({','.join(columns)}) VALUES {','.join(values_strs)};"
    cur.execute(insert_sql)


def sync(dbx, oauth_token):
    create_papers_table()
    citations_info = extract_all_citation_info(dbx)
    update_papers_table(citations_info, oauth_token)
    # rename_files(dbx, citations_info)


def extract_all_citation_info(dbx):
    res = dbx.files_list_folder('')
    citations_info = []
    for file in res.entries:
        path = pathlib.Path(file.name)
        if isinstance(file, FileMetadata):
            if path.suffix == '.pdf':
                citation_info = extract_citation_info(dbx, file)
                if citation_info is not None:
                    citations_info.append((file, citation_info))
            else:
                print(f"Skipping non-PDF file {file.path_display}")
        else:
            print(f"Skipping non-file {path}")
    return citations_info


def rename_files(dbx, citations_info):
    relocation_paths = []
    for file, citation_info in citations_info:
        part_names = [
            'short_title',
            'first_author_last_name',
            'year',
        ]

        parts = extract_parts_for_renaming(citation_info)
        if parts is None:
            print(f"Couldn't find info for {file.name}, skipping")
            continue

        parts = [parts[part_name] for part_name in part_names]
        new_path = '/' + '_'.join(parts) + '.pdf'
        new_path = new_path.replace(" ", "-")

        print(f"{file.path_display} -> {new_path}")
        relocation_path = RelocationPath(from_path=file.path_display, to_path=new_path)
        relocation_paths.append(relocation_path)

    dbx.files_move_batch_v2(relocation_paths)


def make_cite_name(title, authors, venue, year):
    # FIXME: use a something clever here
    first_significant_word = title.split(" ")[0]
    return f"{first_significant_word}{year}"


def split_name(author):
    raise NotImplementedError()
    re.search('\.', author)
    author.split(" ")


def make_last_comma_first(author):
    first, middle_initial, last = split_name(author)
    return f"{last}, {first}"


def format_bibtex_entry(title, authors, venue, year):
    cite_name = make_cite_name(title, authors, venue, year)
    last_firsts = [make_last_comma_first(author) for author in authors]
    authors_string = "and ".join(last_firsts)
    bibtex_parts = [
        "@article {\n",
        cite_name,
        f"title={{{title}}}",
        f"author={{{authors_string}}}",
        f"journal={{{venue}}}",
        f"year={{{year}}}",
        "}\n",
    ]
    bibtex_str = '\n'.join(bibtex_parts)
    return bibtex_str


def generate_bib(dbx, oauth_token):
    res = dbx.files_list_folder('')
    entries = []
    conn = create_connection()
    cur = conn.cursor()
    select_sql = f"SELECT * FROM papers WHERE oauth_token = '{oauth_token}';"
    cur.execute(select_sql)
    rows = cur.fetchall()

    for file in res.entries:
        entry_str = format_bibtex_entry(title, authors, venue, year)
        entries.append(entry_str)

    full_bib_str = '\n\n'.join(entries)
    with open("references.bib", 'w') as f:
        f.write(full_bib_str)


def main():
    token = "l1VJPM_ThysAAAAAAAAAAWTfjrl3jIxgz46lMvaabjQ0d5FQdoZwsLEUEUG-o5Ji"
    with Dropbox(oauth2_access_token=token) as dbx:
        sync(dbx, token)
        # generate_bib(dbx, token)


def create_connection(db_file='reference.db'):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def create_papers_table():
    conn = create_connection()
    create_table_sql = """CREATE TABLE IF NOT EXISTS papers (
                                        id integer PRIMARY KEY,
                                        filename text NOT NULL,
                                        oauth_token text,
                                        title text,
                                        authors text,
                                        venue text,
                                        year text
                                    ); """
    c = conn.cursor()
    c.execute(create_table_sql)

    if conn:
        conn.close()


if __name__ == '__main__':
    # create_papers_table()
    main()

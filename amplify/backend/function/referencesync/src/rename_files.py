import pathlib
import re

from dropbox.files import FileMetadata, RelocationPath

from citation_search import extract_citation_info
from database import create_connection


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
        authors_str = '<author>'.join(citation_info.authors)
        values = [file.path_display, oauth_token, citation_info.title, authors_str, citation_info.venue,
                  citation_info.year]
        values_str = ','.join([f"\"{v}\"" for v in values])
        values_strs.append(f"({values_str})")
    insert_sql = f"INSERT INTO papers ({','.join(columns)}) VALUES {','.join(values_strs)};"
    cur.execute(insert_sql)
    conn.commit()


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

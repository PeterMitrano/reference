import pathlib
import re

from dropbox.files import FileMetadata, RelocationPath

from citation_search import extract_citation_info


def shorten_title(title: str):
    title = title.lower()
    pre_title = title.split(":")[0]
    pre_title.replace(" ", "_")
    words_to_remove = ['the', 'a', 'an', 'and', 'is', 'of', 'if', 'to', 'in', 'on']
    for word in words_to_remove:
        pre_title = pre_title.replace(f" {word} ", " ")
    short_title = pre_title.strip(" ")
    short_title = re.sub(r"[0-9\-,\'\"\(\)]", '', short_title)
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


def extract_all_citation_info(dbx):
    res = dbx.files_list_folder('')
    citations_info = []
    for file in res.entries:
        path = pathlib.Path(file.name)
        file_path: str = file.path_display
        if isinstance(file, FileMetadata):
            if path.suffix == '.pdf':
                citation_info = extract_citation_info(dbx, file)
                if citation_info is not None:
                    citations_info.append((file_path, citation_info))
            else:
                print(f"Skipping non-PDF file {file_path}")
        else:
            print(f"Skipping non-file {path}")
    return citations_info


def rename_file(original_path, citation_info):
    part_names = [
        'short_title',
        'first_author_last_name',
        'year',
    ]

    parts = extract_parts_for_renaming(citation_info)
    if parts is None:
        print(f"Couldn't find info for {original_path}, skipping")
        return None, original_path

    parts = [parts[part_name] for part_name in part_names]
    new_path = '/' + '_'.join(parts) + '.pdf'
    new_path = new_path.replace(" ", "-")

    # print(f"{original_path} -> {new_path}")
    relocation_path = RelocationPath(from_path=original_path, to_path=new_path)
    return relocation_path, new_path


def rename_files(dbx, citations_info):
    relocation_paths = []
    citations_info_renamed = []
    for original_path, citation_info in citations_info:
        relocation_path, new_path = rename_file(original_path, citation_info)
        if relocation_path is not None:
            relocation_paths.append(relocation_path)
        citations_info_renamed.append((new_path, citation_info))

    # FIXME: error handling here?
    dbx.files_move_batch_v2(relocation_paths)

    return citations_info_renamed

import re

from dropbox.files import RelocationPath


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


def parts_for_renaming(citation_info):
    short_title = shorten_title(citation_info.title)
    if len(citation_info.authors) == 0:
        first_author_last_name = ''
    else:
        first_author_last_name = citation_info.authors[0]

    parts = {
        'short_title': short_title,
        'first_author_last_name': first_author_last_name,
        'year': str(citation_info.year),
    }

    return parts


def rename_file(original_path, citation_info):
    part_names = [
        'short_title',
        'first_author_last_name',
        'year',
    ]

    parts = parts_for_renaming(citation_info)

    parts = [parts[part_name] for part_name in part_names]
    new_path = '/' + '_'.join(parts) + '.pdf'
    new_path = new_path.replace(" ", "-")

    relocation_path = RelocationPath(from_path=original_path, to_path=new_path)
    return relocation_path

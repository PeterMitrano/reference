import json
from time import time

from dropbox import Dropbox

from bib import generate_bib
from citation_search import extract_citation_info, DEFAULT_CONFIDENCE_THRESHOLD
from database import check_paper, create_paper
from dropbox_utils import get_pdf_files
from rename_files import rename_file


def get_dropbox_token(event):
    args = event['arguments']
    dropbox_oauth_token = args['dropbox_oauth_token']
    return dropbox_oauth_token


def update_papers_table(dbx, dropbox_oauth_token):
    relocation_paths = []
    for pdf_file, original_path in get_pdf_files(dbx):
        exists = check_paper(dropbox_oauth_token, original_path)
        if not exists:
            citation_info = extract_citation_info(dbx, pdf_file)

            if citation_info.confidence > DEFAULT_CONFIDENCE_THRESHOLD:
                relocation_path = rename_file(original_path, citation_info)
                if relocation_path.from_path != relocation_path.to_path:
                    relocation_paths.append(relocation_path)
                new_path = relocation_path.from_path
            else:
                new_path = original_path

            create_paper(new_path, citation_info, dropbox_oauth_token)

    # finally, run all the RelocationPath calls
    if len(relocation_paths) > 0:
        # FIXME: error handling here?
        print("relocating files")
        dbx.files_move_batch_v2(relocation_paths)


def sync(event):
    dropbox_oauth_token = get_dropbox_token(event)

    with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
        update_papers_table(dbx, dropbox_oauth_token)

    bib_text = generate_bib(dropbox_oauth_token)

    return {
        'generated_at': str(int(time())),
        'text': bib_text,
    }


def regenerate(event):
    dropbox_oauth_token = get_dropbox_token(event)
    bib_text = generate_bib(dropbox_oauth_token)
    return {
        'generated_at': str(int(time())),
        'text': bib_text,
    }


def handler(event, context):
    field_name = event['fieldName']

    if field_name == 'sync':
        return sync(event)
    elif field_name == 'regenerate':
        return regenerate(event)
    else:
        return {
            'generated_at': str(int(time())),
            'text': f'Error: undefined {field_name=}',
        }


if __name__ == '__main__':
    with open('event.json') as f:
        event = json.load(f)
    handler(event, None)

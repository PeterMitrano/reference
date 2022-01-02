import json
from time import time

from dropbox import Dropbox

from bib import generate_bib
from database import update_papers_table, delete_papers
from debugging import RemoteDebugSession
from rename_files import extract_all_citation_info, rename_files


def get_dropbox_token(event):
    args = event['arguments']
    dropbox_oauth_token = args['dropbox_oauth_token']
    return dropbox_oauth_token


def sync(event):
    dropbox_oauth_token = get_dropbox_token(event)

    success = delete_papers(dropbox_oauth_token)
    if not success:
        print("Failed to delete papers")
        return ''

    with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
        citations_info = extract_all_citation_info(dbx)
        citations_info = rename_files(dbx, citations_info)

    update_papers_table(citations_info, dropbox_oauth_token)

    bib_text = generate_bib(dropbox_oauth_token)

    # TODO: update the user to store the latest bib text?

    print('returning bib_text')
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
